import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from backend.crawler.web_crawler_base import WebCrawlerBase, CrawlResult
from backend.crawler.algorithms.bfs_crawler import BFSCrawler
from backend.crawler.algorithms.dfs_crawler import DFSCrawler
from datetime import datetime

@pytest.fixture
def crawler_config():
    return {
        'seed_urls': ['https://example.com'],
        'max_pages': 10,
        'max_depth': 2,
        'crawl_delay': 0.1,
        'user_agent': 'TestBot/1.0',
        'allowed_domains': ['example.com'],
        'max_concurrent_requests': 5,
        'request_timeout': 10
    }

@pytest.fixture
def bfs_crawler(crawler_config):
    return BFSCrawler(crawler_config)

@pytest.fixture
def dfs_crawler(crawler_config):
    return DFSCrawler(crawler_config)

class TestWebCrawlerBase:
    
    def test_init(self, bfs_crawler):
        """Test crawler initialization"""
        assert not bfs_crawler.is_crawling
        assert len(bfs_crawler.visited_urls) == 0
        assert len(bfs_crawler.results) == 0
    
    def test_is_valid_url(self, bfs_crawler):
        """Test URL validation"""
        # Valid URLs
        assert bfs_crawler.is_valid_url('https://example.com')
        assert bfs_crawler.is_valid_url('https://sub.example.com')
        assert bfs_crawler.is_valid_url('http://example.com/path')
        
        # Invalid URLs
        assert not bfs_crawler.is_valid_url('ftp://example.com')
        assert not bfs_crawler.is_valid_url('https://other.com')
        assert not bfs_crawler.is_valid_url('not-a-url')
        assert not bfs_crawler.is_valid_url('')
    
    def test_extract_domain(self, bfs_crawler):
        """Test domain extraction"""
        assert bfs_crawler.extract_domain('https://example.com') == 'example.com'
        assert bfs_crawler.extract_domain('https://www.example.com') == 'example.com'
        assert bfs_crawler.extract_domain('http://sub.example.com/path') == 'sub.example.com'
    
    def test_extract_links(self, bfs_crawler):
        """Test link extraction from HTML"""
        html = '''
        <html>
            <body>
                <a href="https://example.com/page1">Page 1</a>
                <a href="/page2">Page 2</a>
                <a href="../page3">Page 3</a>
                <a href="https://other.com/page4">External</a>
                <a href="mailto:test@example.com">Email</a>
                <a>No href</a>
            </body>
        </html>
        '''
        
        base_url = 'https://example.com/dir/'
        links = bfs_crawler.extract_links(html, base_url)
        
        # Should include valid internal links only
        expected_links = [
            'https://example.com/page1',
            'https://example.com/page2',
            'https://example.com/page3'
        ]
        
        for link in expected_links:
            assert link in links
        
        # Should not include external or invalid links
        assert 'https://other.com/page4' not in links
        assert 'mailto:test@example.com' not in links
    
    def test_extract_content(self, bfs_crawler):
        """Test content extraction from HTML"""
        html = '''
        <html>
            <head>
                <title>Test Page Title</title>
                <script>console.log('test');</script>
            </head>
            <body>
                <nav>Navigation</nav>
                <header>Header</header>
                <main>
                    <h1>Main Heading</h1>
                    <p>This is the main content of the page.</p>
                </main>
                <footer>Footer</footer>
                <style>.test { color: red; }</style>
            </body>
        </html>
        '''
        
        title, content = bfs_crawler.extract_content(html)
        
        assert title == "Test Page Title"
        assert "Main Heading" in content
        assert "main content" in content
        assert "Navigation" not in content  # Should be removed
        assert "console.log" not in content  # Script should be removed
        assert ".test" not in content  # Style should be removed
    
    @pytest.mark.asyncio
    async def test_crawl_url_success(self, bfs_crawler):
        """Test successful URL crawling"""
        test_html = '''
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Content</h1>
                <a href="https://example.com/link1">Link 1</a>
            </body>
        </html>
        '''
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=test_html)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await bfs_crawler.crawl_url('https://example.com', 0)
            
            assert result is not None
            assert result.url == 'https://example.com'
            assert result.title == 'Test Page'
            assert 'Test Content' in result.content
            assert result.status_code == 200
            assert result.depth == 0
    
    @pytest.mark.asyncio
    async def test_crawl_url_failure(self, bfs_crawler):
        """Test URL crawling with HTTP error"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await bfs_crawler.crawl_url('https://example.com/404', 0)
            
            assert result is None

class TestBFSCrawler:
    
    @pytest.mark.asyncio
    async def test_bfs_crawl(self, bfs_crawler):
        """Test BFS crawling algorithm"""
        # Mock HTML responses
        html_responses = {
            'https://example.com': '''
                <html>
                    <head><title>Home</title></head>
                    <body>
                        <a href="https://example.com/page1">Page 1</a>
                        <a href="https://example.com/page2">Page 2</a>
                    </body>
                </html>
            ''',
            'https://example.com/page1': '''
                <html>
                    <head><title>Page 1</title></head>
                    <body><p>Content of page 1</p></body>
                </html>
            ''',
            'https://example.com/page2': '''
                <html>
                    <head><title>Page 2</title></head>
                    <body><p>Content of page 2</p></body>
                </html>
            '''
        }
        
        async def mock_get(url):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_responses.get(str(url), ''))
            return mock_response
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            results = await bfs_crawler.crawl(['https://example.com'])
            
            assert len(results) >= 1  # At least the seed URL
            assert any(r.url == 'https://example.com' for r in results)

class TestDFSCrawler:
    
    @pytest.mark.asyncio
    async def test_dfs_crawl(self, dfs_crawler):
        """Test DFS crawling algorithm"""
        # Mock HTML responses
        html_responses = {
            'https://example.com': '''
                <html>
                    <head><title>Home</title></head>
                    <body>
                        <a href="https://example.com/page1">Page 1</a>
                    </body>
                </html>
            ''',
            'https://example.com/page1': '''
                <html>
                    <head><title>Page 1</title></head>
                    <body><p>Deep content</p></body>
                </html>
            '''
        }
        
        async def mock_get(url):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_responses.get(str(url), ''))
            return mock_response
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            results = await dfs_crawler.crawl(['https://example.com'])
            
            assert len(results) >= 1  # At least the seed URL
            assert any(r.url == 'https://example.com' for r in results)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
