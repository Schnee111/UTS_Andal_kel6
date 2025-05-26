import asyncio
import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import logging

from crawler.web_crawler import WebCrawler
from crawler.search_engine import SearchEngine
from config import Config

# Initialize FastAPI app
app = FastAPI(
    title="Internal Web Search Engine API",
    description="REST API for internal web crawling and search",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
config = Config()
crawler = WebCrawler(config.get_crawler_config())
search_engine = SearchEngine(config.DATABASE_PATH, config.CACHE_TTL)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/search_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class ConfigUpdate(BaseModel):
    seed_urls: Optional[List[str]] = None
    max_pages: Optional[int] = None
    max_depth: Optional[int] = None
    crawl_delay: Optional[float] = None
    user_agent: Optional[str] = None
    allowed_domains: Optional[List[str]] = None
    cache_enabled: Optional[bool] = None
    allowed_domains: Optional[List[str]] = None
    cache_enabled: Optional[bool] = None
    cache_ttl: Optional[int] = None

# Background task for crawling
crawl_task = None

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("database", exist_ok=True)
    os.makedirs("deliverables", exist_ok=True)
    
    logger.info("Search Engine API started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if crawler.is_crawling:
        crawler.stop_crawling()
    logger.info("Search Engine API stopped")

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Internal Web Search Engine API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/config")
async def get_config():
    """Get current configuration"""
    return config.get_all_config()

@app.put("/config")
async def update_config(config_update: ConfigUpdate):
    """Update configuration"""
    try:
        updates = config_update.dict(exclude_unset=True)
        config.update_config(updates)
        
        # Update crawler config
        global crawler
        crawler = WebCrawler(config.get_crawler_config())
        
        # Update search engine cache TTL
        if 'cache_ttl' in updates:
            search_engine.cache_ttl = config.CACHE_TTL
        
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/crawl/start")
async def start_crawl(background_tasks: BackgroundTasks):
    """Start crawling process"""
    global crawl_task
    
    if crawler.is_crawling:
        raise HTTPException(status_code=400, detail="Crawling is already in progress")
    
    try:
        # Start crawling in background
        crawl_task = asyncio.create_task(run_crawl())
        
        return {"message": "Crawling started"}
    except Exception as e:
        logger.error(f"Error starting crawl: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_crawl():
    """Run the crawling process"""
    try:
        seed_urls = config.SEED_URLS
        algorithm = config.CRAWL_ALGORITHM
        
        logger.info(f"Starting {algorithm} crawl with {len(seed_urls)} seed URLs")
        
        if algorithm.lower() == 'dfs':
            results = await crawler.crawl_dfs(seed_urls)
        else:
            results = await crawler.crawl_bfs(seed_urls)
        
        # Store results in database
        if results:
            search_engine.store_pages(results)
            logger.info(f"Crawling completed. Stored {len(results)} pages")
        
    except Exception as e:
        logger.error(f"Error during crawling: {e}")

@app.post("/crawl/stop")
async def stop_crawl():
    """Stop crawling process"""
    crawler.stop_crawling()
    return {"message": "Crawling stopped"}

@app.get("/crawl/status")
async def get_crawl_status():
    """Get current crawling status"""
    return crawler.get_status()

@app.post("/search")
async def search(request: SearchRequest):
    """Search for pages"""
    try:
        cache_enabled = config.CACHE_ENABLED
        results = search_engine.search(
            query=request.query,
            limit=request.limit,
            use_cache=cache_enabled
        )
        return results
    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_search_history():
    """Get search history"""
    try:
        return search_engine.get_search_history()
    except Exception as e:
        logger.error(f"Error getting search history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get search engine statistics"""
    try:
        stats = search_engine.get_stats()
        # Add current crawl status
        crawl_status = crawler.get_status()
        stats['crawl_status'] = crawl_status['status']
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/clear")
async def clear_cache():
    """Clear search cache"""
    try:
        deleted = search_engine.clear_cache()
        return {"message": f"Cleared {deleted} cache entries"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export/pages")
async def export_pages():
    """Export all crawled pages as JSON"""
    try:
        import sqlite3
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT url, title, content, crawl_time, depth, parent_url 
            FROM pages ORDER BY crawl_time DESC
        ''')
        
        pages = []
        for row in cursor.fetchall():
            pages.append({
                'url': row[0],
                'title': row[1],
                'content': row[2],
                'crawl_time': row[3],
                'depth': row[4],
                'parent_url': row[5]
            })
        
        conn.close()
        
        # Save to file
        export_path = "deliverables/exported_pages.json"
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(pages, f, indent=2, ensure_ascii=False)
        
        return FileResponse(
            export_path,
            media_type='application/json',
            filename='exported_pages.json'
        )
    except Exception as e:
        logger.error(f"Error exporting pages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
