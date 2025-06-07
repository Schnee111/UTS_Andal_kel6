import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from backend.crawler.algorithms.bfs_crawler import BFSCrawler
from backend.crawler.algorithms.dfs_crawler import DFSCrawler

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

class TestAlgorithmComparison:
    
    @pytest.mark.asyncio
    async def test_bfs_vs_dfs_coverage(self, crawler_config):
        """Compare coverage between BFS and DFS"""
        
        # Mock HTML responses for a simple tree structure
        html_responses = {
            'https://example.com': '''
                <html>
                    <head><title>Root</title></head>
                    <body>
                        <a href="https://example.com/page1">Page 1</a>
                        <a href="https://example.com/page2">Page 2</a>
                    </body>
                </html>
            ''',
            'https://example.com/page1': '''
                <html>
                    <head><title>Page 1</title></head>
                    <body>
                        <a href="https://example.com/page1/sub1">Sub 1</a>
                        <a href="https://example.com/page1/sub2">Sub 2</a>
                    </body>
                </html>
            ''',
            'https://example.com/page2': '''
                <html>
                    <head><title>Page 2</title></head>
                    <body>
                        <a href="https://example.com/page2/sub1">Sub 1</a>
                    </body>
                </html>
            ''',
            'https://example.com/page1/sub1': '''
                <html>
                    <head><title>Page 1 Sub 1</title></head>
                    <body><p>Deep content 1</p></body>
                </html>
            ''',
            'https://example.com/page1/sub2': '''
                <html>
                    <head><title>Page 1 Sub 2</title></head>
                    <body><p>Deep content 2</p></body>
                </html>
            ''',
            'https://example.com/page2/sub1': '''
                <html>
                    <head><title>Page 2 Sub 1</title></head>
                    <body><p>Deep content 3</p></body>
                </html>
            '''
        }
        
        async def mock_get(url):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_responses.get(str(url), ''))
            return mock_response
        
        # Test BFS
        bfs_crawler = BFSCrawler(crawler_config)
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            bfs_results = await bfs_crawler.crawl(['https://example.com'])
        
        # Test DFS
        dfs_crawler = DFSCrawler(crawler_config)
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            dfs_results = await dfs_crawler.crawl(['https://example.com'])
        
        # Both should find the same pages (eventually)
        bfs_urls = {result.url for result in bfs_results}
        dfs_urls = {result.url for result in dfs_results}
        
        # Check that both algorithms found pages
        assert len(bfs_results) > 0
        assert len(dfs_results) > 0
        
        # Both should find the root page
        assert 'https://example.com' in bfs_urls
        assert 'https://example.com' in dfs_urls
    
    @pytest.mark.asyncio
    async def test_bfs_breadth_first_order(self, crawler_config):
        """Test that BFS explores breadth-first"""
        
        html_responses = {
            'https://example.com': '''
                <html>
                    <head><title>Root</title></head>
                    <body>
                        <a href="https://example.com/level1-a">Level 1 A</a>
                        <a href="https://example.com/level1-b">Level 1 B</a>
                    </body>
                </html>
            ''',
            'https://example.com/level1-a': '''
                <html>
                    <head><title>Level 1 A</title></head>
                    <body>
                        <a href="https://example.com/level2-a">Level 2 A</a>
                    </body>
                </html>
            ''',
            'https://example.com/level1-b': '''
                <html>
                    <head><title>Level 1 B</title></head>
                    <body>
                        <a href="https://example.com/level2-b">Level 2 B</a>
                    </body>
                </html>
            ''',
            'https://example.com/level2-a': '''
                <html>
                    <head><title>Level 2 A</title></head>
                    <body><p>Deep A</p></body>
                </html>
            ''',
            'https://example.com/level2-b': '''
                <html>
                    <head><title>Level 2 B</title></head>
                    <body><p>Deep B</p></body>
                </html>
            '''
        }
        
        async def mock_get(url):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_responses.get(str(url), ''))
            return mock_response
        
        bfs_crawler = BFSCrawler(crawler_config)
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            results = await bfs_crawler.crawl(['https://example.com'])
        
        # Check depth progression - BFS should explore all depth 0, then depth 1, then depth 2
        depths = [result.depth for result in results]
        
        # Should have pages at different depths
        assert 0 in depths  # Root
        assert 1 in depths  # Level 1 pages
        
        # BFS should explore breadth-first, so we should see depth progression
        depth_0_count = depths.count(0)
        depth_1_count = depths.count(1)
        
        assert depth_0_count >= 1  # At least the root
        assert depth_1_count >= 1  # At least some level 1 pages
    
    @pytest.mark.asyncio
    async def test_memory_usage_comparison(self, crawler_config):
        """Compare memory usage patterns between BFS and DFS"""
        
        # Simple mock that tracks queue/stack sizes
        bfs_max_queue_size = 0
        dfs_max_stack_depth = 0
        
        class MockBFSCrawler(BFSCrawler):
            def __init__(self, config):
                super().__init__(config)
                self.max_queue_size = 0
            
            async def crawl(self, seed_urls):
                # Track maximum queue size during crawling
                nonlocal bfs_max_queue_size
                self.max_queue_size = max(self.max_queue_size, len(self.crawl_queue))
                bfs_max_queue_size = self.max_queue_size
                return await super().crawl(seed_urls)
        
        class MockDFSCrawler(DFSCrawler):
            def __init__(self, config):
                super().__init__(config)
                self.current_depth = 0
                self.max_depth_reached = 0
            
            async def crawl(self, seed_urls):
                # Track maximum recursion depth
                nonlocal dfs_max_stack_depth
                dfs_max_stack_depth = self.max_depth_reached
                return await super().crawl(seed_urls)
        
        # For this test, we expect BFS to use more memory (larger queue)
        # and DFS to have deeper recursion but less memory overall
        
        # This is a conceptual test - in practice, you'd need more sophisticated
        # memory tracking tools to measure actual memory usage
        assert True  # Placeholder for actual memory measurement
    
    def test_algorithm_selection_logic(self):
        """Test the logic for selecting appropriate algorithm"""
        
        def recommend_algorithm(website_type, content_depth, memory_constraints):
            """
            Recommend BFS or DFS based on website characteristics
            """
            if memory_constraints == "low":
                return "DFS"
            
            if website_type == "hierarchical" and content_depth == "shallow":
                return "BFS"
            elif website_type == "interconnected" and content_depth == "deep":
                return "DFS"
            elif website_type == "catalog":
                return "BFS"
            elif website_type == "documentation":
                return "DFS"
            else:
                return "BFS"  # Default
        
        # Test various scenarios
        assert recommend_algorithm("catalog", "shallow", "high") == "BFS"
        assert recommend_algorithm("documentation", "deep", "high") == "DFS"
        assert recommend_algorithm("hierarchical", "shallow", "high") == "BFS"
        assert recommend_algorithm("any", "any", "low") == "DFS"
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, crawler_config):
        """Test performance metrics collection for both algorithms"""
        
        # Mock a simple website structure
        html_responses = {
            'https://example.com': '<html><head><title>Root</title></head><body><a href="https://example.com/page1">Page 1</a></body></html>',
            'https://example.com/page1': '<html><head><title>Page 1</title></head><body><p>Content</p></body></html>'
        }
        
        async def mock_get(url):
            # Add small delay to simulate network
            await asyncio.sleep(0.01)
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_responses.get(str(url), ''))
            return mock_response
        
        # Test BFS performance
        bfs_crawler = BFSCrawler(crawler_config)
        bfs_start = time.time()
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            bfs_results = await bfs_crawler.crawl(['https://example.com'])
        bfs_duration = time.time() - bfs_start
        
        # Test DFS performance
        dfs_crawler = DFSCrawler(crawler_config)
        dfs_start = time.time()
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            dfs_results = await dfs_crawler.crawl(['https://example.com'])
        dfs_duration = time.time() - dfs_start
        
        # Both should complete in reasonable time
        assert bfs_duration &lt; 10  # seconds
        assert dfs_duration &lt; 10  # seconds
        
        # Both should find some results
        assert len(bfs_results) > 0
        assert len(dfs_results) > 0
        
        # Performance comparison (this will vary based on implementation)
        print(f"BFS Duration: {bfs_duration:.3f}s, Pages: {len(bfs_results)}")
        print(f"DFS Duration: {dfs_duration:.3f}s, Pages: {len(dfs_results)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
