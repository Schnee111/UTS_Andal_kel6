import pytest
import tempfile
import os
from datetime import datetime, timedelta
from crawler.search_engine import SearchEngine
from crawler.web_crawler import CrawlResult

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)

@pytest.fixture
def search_engine(temp_db):
    """Create search engine with temporary database"""
    return SearchEngine(temp_db, cache_ttl=3600)

@pytest.fixture
def sample_crawl_results():
    """Create sample crawl results for testing"""
    return [
        CrawlResult(
            url="https://example.com/page1",
            title="Python Programming Tutorial",
            content="Learn Python programming language. Python is a powerful programming language used for web development, data science, and automation.",
            links=["https://example.com/page2"],
            status_code=200,
            crawl_time=datetime.now(),
            depth=0
        ),
        CrawlResult(
            url="https://example.com/page2",
            title="Web Development with Python",
            content="Build web applications using Python frameworks like Django and Flask. Web development is an important skill for programmers.",
            links=["https://example.com/page3"],
            status_code=200,
            crawl_time=datetime.now(),
            depth=1,
            parent_url="https://example.com/page1"
        ),
        CrawlResult(
            url="https://example.com/page3",
            title="Data Science Introduction",
            content="Data science involves extracting insights from data using statistical methods and machine learning algorithms.",
            links=[],
            status_code=200,
            crawl_time=datetime.now(),
            depth=2,
            parent_url="https://example.com/page2"
        )
    ]

class TestSearchEngine:
    
    def test_init(self, search_engine):
        """Test search engine initialization"""
        assert search_engine.db_path is not None
        assert search_engine.cache_ttl == 3600
        assert search_engine.vectorizer is not None
    
    def test_clean_text(self, search_engine):
        """Test text cleaning function"""
        text = "  Hello, World!  This is a TEST.  "
        cleaned = search_engine.clean_text(text)
        
        assert cleaned == "hello world this is a test"
        assert "," not in cleaned
        assert "!" not in cleaned
        assert "." not in cleaned
    
    def test_store_pages(self, search_engine, sample_crawl_results):
        """Test storing crawl results in database"""
        search_engine.store_pages(sample_crawl_results)
        
        # Check if pages were stored
        import sqlite3
        conn = sqlite3.connect(search_engine.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM pages")
        count = cursor.fetchone()[0]
        assert count == len(sample_crawl_results)
        
        cursor.execute("SELECT url, title FROM pages ORDER BY url")
        stored_pages = cursor.fetchall()
        
        for i, (url, title) in enumerate(stored_pages):
            assert url == sample_crawl_results[i].url
            assert title == sample_crawl_results[i].title
        
        conn.close()
    
    def test_search_functionality(self, search_engine, sample_crawl_results):
        """Test search functionality"""
        # Store sample data
        search_engine.store_pages(sample_crawl_results)
        
        # Test search for Python
        results = search_engine.search("Python programming", limit=5)
        
        assert "results" in results
        assert "total_found" in results
        assert "execution_time_ms" in results
        assert "cached" in results
        
        # Should find pages containing Python
        assert len(results["results"]) > 0
        assert any("Python" in result["title"] or "python" in result["content_snippet"].lower() 
                  for result in results["results"])
    
    def test_search_with_no_results(self, search_engine, sample_crawl_results):
        """Test search with query that returns no results"""
        search_engine.store_pages(sample_crawl_results)
        
        results = search_engine.search("nonexistent query xyz123", limit=5)
        
        assert results["total_found"] == 0
        assert len(results["results"]) == 0
    
    def test_search_caching(self, search_engine, sample_crawl_results):
        """Test search result caching"""
        search_engine.store_pages(sample_crawl_results)
        
        query = "Python programming"
        
        # First search (not cached)
        results1 = search_engine.search(query, limit=5, use_cache=True)
        assert not results1["cached"]
        
        # Second search (should be cached)
        results2 = search_engine.search(query, limit=5, use_cache=True)
        assert results2["cached"]
        
        # Results should be the same
        assert len(results1["results"]) == len(results2["results"])
    
    def test_cache_expiration(self, search_engine, sample_crawl_results):
        """Test cache expiration"""
        # Set very short cache TTL
        search_engine.cache_ttl = 1
        search_engine.store_pages(sample_crawl_results)
        
        query = "Python programming"
        
        # First search
        results1 = search_engine.search(query, use_cache=True)
        assert not results1["cached"]
        
        # Wait for cache to expire
        import time
        time.sleep(2)
        
        # Search again (cache should be expired)
        results2 = search_engine.search(query, use_cache=True)
        assert not results2["cached"]
    
    def test_get_page_route(self, search_engine, sample_crawl_results):
        """Test page route tracking"""
        search_engine.store_pages(sample_crawl_results)
        
        # Get route for the deepest page
        import sqlite3
        conn = sqlite3.connect(search_engine.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM pages WHERE url = ?", ("https://example.com/page3",))
        page_id = cursor.fetchone()[0]
        conn.close()
        
        route = search_engine.get_page_route(page_id)
        
        assert len(route) == 3  # Should have 3 pages in route
        assert route[0]["url"] == "https://example.com/page1"
        assert route[1]["url"] == "https://example.com/page2"
        assert route[2]["url"] == "https://example.com/page3"
    
    def test_search_history(self, search_engine, sample_crawl_results):
        """Test search history tracking"""
        search_engine.store_pages(sample_crawl_results)
        
        # Perform some searches
        search_engine.search("Python", limit=5)
        search_engine.search("web development", limit=5)
        
        # Get search history
        history = search_engine.get_search_history()
        
        assert len(history) >= 2
        assert any(h["query"] == "Python" for h in history)
        assert any(h["query"] == "web development" for h in history)
        
        # Check history structure
        for item in history:
            assert "query" in item
            assert "results_count" in item
            assert "execution_time" in item
            assert "cached" in item
            assert "searched_at" in item
    
    def test_get_stats(self, search_engine, sample_crawl_results):
        """Test statistics retrieval"""
        search_engine.store_pages(sample_crawl_results)
        search_engine.search("Python", limit=5)
        
        stats = search_engine.get_stats()
        
        assert "total_pages" in stats
        assert "total_searches" in stats
        assert "cached_queries" in stats
        assert "database_size" in stats
        assert "index_size" in stats
        
        assert stats["total_pages"] == len(sample_crawl_results)
        assert stats["total_searches"] >= 1
    
    def test_clear_cache(self, search_engine, sample_crawl_results):
        """Test cache clearing"""
        search_engine.store_pages(sample_crawl_results)
        
        # Create some cached results
        search_engine.search("Python", use_cache=True)
        search_engine.search("web", use_cache=True)
        
        # Clear cache
        deleted = search_engine.clear_cache()
        assert deleted >= 0
        
        # Verify cache is cleared
        import sqlite3
        conn = sqlite3.connect(search_engine.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM search_cache")
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 0

def test_search_integration():
    """Integration test for search functionality"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
        db_path = temp_file.name
    
    try:
        search_engine = SearchEngine(db_path)
        
        # Create test data
        test_results = [
            CrawlResult(
                url="https://test.com/ai",
                title="Artificial Intelligence Guide",
                content="Artificial intelligence and machine learning are transforming technology. AI algorithms can process data and make decisions.",
                links=[],
                status_code=200,
                crawl_time=datetime.now(),
                depth=0
            ),
            CrawlResult(
                url="https://test.com/ml",
                title="Machine Learning Basics",
                content="Machine learning is a subset of artificial intelligence. ML models learn from data to make predictions.",
                links=[],
                status_code=200,
                crawl_time=datetime.now(),
                depth=0
            )
        ]
        
        # Store and search
        search_engine.store_pages(test_results)
        results = search_engine.search("artificial intelligence")
        
        assert len(results["results"]) > 0
        assert results["total_found"] > 0
        
        # Check result structure
        for result in results["results"]:
            assert "url" in result
            assert "title" in result
            assert "content_snippet" in result
            assert "similarity_score" in result
            assert "route" in result
            assert "last_crawled" in result
    
    finally:
        os.unlink(db_path)
