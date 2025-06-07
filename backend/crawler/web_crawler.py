import asyncio
import aiohttp
import time
from urllib.parse import urljoin, urlparse
from collections import deque
from bs4 import BeautifulSoup
from typing import List, Dict, Set, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CrawlResult:
    url: str
    title: str
    content: str
    links: List[str]
    status_code: int
    crawl_time: datetime
    depth: int
    parent_url: Optional[str] = None

class WebCrawler:
    def __init__(self, config: Dict):
        self.config = config
        self.visited_urls: Set[str] = set()
        self.crawl_queue = deque()
        self.results: List[CrawlResult] = []
        self.is_crawling = False
        self.current_url = None
        self.start_time = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
       
    async def create_session(self):
        """Create aiohttp session with proper headers"""
        headers = {
            'User-Agent': self.config.get('user_agent', 'InternalSearchBot/1.0'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
        )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and within allowed domains"""
        try:
            parsed = urlparse(url)
            
            # Check if URL has proper scheme and netloc
            if not parsed.netloc or parsed.scheme not in ['http', 'https']:
                return False
            
            # Check allowed domains
            allowed_domains = self.config.get('allowed_domains', [])
            if allowed_domains:
                domain = parsed.netloc.lower()
                # Remove www. prefix for comparison
                if domain.startswith('www.'):
                    domain = domain[4:]
                
                allowed = False
                for allowed_domain in allowed_domains:
                    allowed_domain = allowed_domain.lower()
                    if allowed_domain.startswith('www.'):
                        allowed_domain = allowed_domain[4:]
                    
                    if domain == allowed_domain or domain.endswith('.' + allowed_domain):
                        allowed = True
                        break
                
                if not allowed:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating URL {url}: {e}")
            return False
    
    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """Extract all links from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, href)
                
                # Clean up URL (remove fragments)
                parsed = urlparse(absolute_url)
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    clean_url += f"?{parsed.query}"
                
                if self.is_valid_url(clean_url):
                    links.append(clean_url)
            
            return list(set(links))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error extracting links from {base_url}: {e}")
            return []
    
    def extract_content(self, html_content: str) -> Tuple[str, str]:
        """Extract title and text content from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "No Title"
            
            # Remove script, style, and other non-content tags
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            # Extract text content
            content = soup.get_text()
            
            # Clean up content
            lines = [line.strip() for line in content.splitlines()]
            content = ' '.join(line for line in lines if line)
            
            return title, content
            
        except Exception as e:
            self.logger.error(f"Error extracting content: {e}")
            return "No Title", ""
    
    async def crawl_url(self, url: str, depth: int, parent_url: Optional[str] = None) -> Optional[CrawlResult]:
        """Crawl a single URL"""
        if not self.session:
            await self.create_session()
        
        try:
            self.current_url = url
            self.logger.info(f"Crawling: {url} (depth: {depth})")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    title, content = self.extract_content(html_content)
                    links = self.extract_links(html_content, url)
                    
                    result = CrawlResult(
                        url=url,
                        title=title,
                        content=content,
                        links=links,
                        status_code=response.status,
                        crawl_time=datetime.now(),
                        depth=depth,
                        parent_url=parent_url
                    )
                    
                    return result
                else:
                    self.logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout crawling {url}")
            return None
        except Exception as e:
            self.logger.error(f"Error crawling {url}: {e}")
            return None
    
    async def crawl_bfs(self, seed_urls: List[str]) -> List[CrawlResult]:
        """Crawl using Breadth-First Search algorithm"""
        self.is_crawling = True
        self.start_time = datetime.now()
        self.visited_urls.clear()
        self.results.clear()
        
        # Initialize queue with seed URLs
        for seed_url in seed_urls:
            if self.is_valid_url(seed_url):
                self.crawl_queue.append((seed_url, 0, None))
        
        max_pages = self.config.get('max_pages', 100)
        max_depth = self.config.get('max_depth', 3)
        crawl_delay = self.config.get('crawl_delay', 1.0)
        
        try:
            await self.create_session()
            
            while self.crawl_queue and len(self.results) < max_pages and self.is_crawling:
                url, depth, parent_url = self.crawl_queue.popleft()
                
                if url in self.visited_urls or depth > max_depth:
                    continue
                
                self.visited_urls.add(url)
                
                # Crawl the URL
                result = await self.crawl_url(url, depth, parent_url)
                
                if result:
                    self.results.append(result)
                    self.logger.info(f"Crawled {len(self.results)}/{max_pages}: {url}")
                    
                    # Add found links to queue for next depth level
                    if depth < max_depth:
                        for link in result.links:
                            if link not in self.visited_urls:
                                self.crawl_queue.append((link, depth + 1, url))
                
                # Add delay between requests
                if crawl_delay > 0:
                    await asyncio.sleep(crawl_delay)
        
        finally:
            await self.close_session()
            self.is_crawling = False
            self.current_url = None
        
        self.logger.info(f"Crawling completed. Found {len(self.results)} pages.")
        return self.results
    
    async def crawl_dfs(self, seed_urls: List[str]) -> List[CrawlResult]:
        """Crawl using Depth-First Search algorithm"""
        self.is_crawling = True
        self.start_time = datetime.now()
        self.visited_urls.clear()
        self.results.clear()
        
        max_pages = self.config.get('max_pages', 100)
        max_depth = self.config.get('max_depth', 3)
        crawl_delay = self.config.get('crawl_delay', 1.0)
        
        async def dfs_recursive(url: str, depth: int, parent_url: Optional[str] = None):
            if (len(self.results) >= max_pages or 
                depth > max_depth or 
                url in self.visited_urls or 
                not self.is_crawling):
                return
            
            self.visited_urls.add(url)
            
            # Crawl the URL
            result = await self.crawl_url(url, depth, parent_url)
            
            if result:
                self.results.append(result)
                self.logger.info(f"Crawled {len(self.results)}/{max_pages}: {url}")
                
                # Add delay between requests
                if crawl_delay > 0:
                    await asyncio.sleep(crawl_delay)
                
                # Recursively crawl found links
                for link in result.links:
                    if len(self.results) < max_pages and self.is_crawling:
                        await dfs_recursive(link, depth + 1, url)
        
        try:
            await self.create_session()
            
            # Start DFS from each seed URL
            for seed_url in seed_urls:
                if self.is_valid_url(seed_url) and len(self.results) < max_pages:
                    await dfs_recursive(seed_url, 0)
        
        finally:
            await self.close_session()
            self.is_crawling = False
            self.current_url = None
        
        self.logger.info(f"DFS Crawling completed. Found {len(self.results)} pages.")
        return self.results
    
    def stop_crawling(self):
        """Stop the crawling process"""
        self.is_crawling = False
        self.logger.info("Crawling stopped by user")
    
    def get_status(self) -> Dict:
        """Get current crawling status"""
        total_pages = self.config.get('max_pages', 100)
        pages_crawled = len(self.results)
        progress = (pages_crawled / total_pages * 100) if total_pages > 0 else 0
        
        status = {
            'status': 'crawling' if self.is_crawling else ('completed' if self.results else 'idle'),
            'pages_crawled': pages_crawled,
            'total_pages': total_pages,
            'progress_percentage': progress,
            'current_url': self.current_url,
        }
        
        if self.start_time:
            status['start_time'] = self.start_time.isoformat()
            
            if self.is_crawling and pages_crawled > 0:
                # Estimate completion time
                elapsed = (datetime.now() - self.start_time).total_seconds()
                estimated_total = (elapsed / pages_crawled) * total_pages
                estimated_completion = self.start_time.timestamp() + estimated_total
                status['estimated_completion'] = datetime.fromtimestamp(estimated_completion).isoformat()
        
        return status
