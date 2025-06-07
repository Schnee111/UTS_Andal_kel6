import pytest
import tempfile
import os
from datetime import datetime
from backend.search.search_manager import SearchManager
from backend.search.database.db_manager import DatabaseManager
from backend.search.indexing.tfidf_indexer import TFIDFIndexer
from backend.crawler.web_crawler_base import CrawlResult

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)

@pytest.fixture
def db_manager(temp_db):
    """Create database manager with temporary database"""
    return DatabaseManager(temp_db)

@pytest.fixture
def tfidf_indexer():
    """Create TF-IDF indexer"""
    return TFIDFIndexer()

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
            depth=0,
            domain="example.com"
        ),
        CrawlResult(
            url="https://example.com/page2",
            title="Web Development with Python",
            content="Build web applications using Python frameworks like Django and Flask. Web development is an important skill for programmers.",
            links=["https://example.com/page3"],
            status_code=200,
            crawl_time=datetime.now(),
            depth=1,
            domain="example.com",
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
            domain="example.com",
            parent_url="https://example.com/page2"
        )
    ]

class TestDatabaseManager:
    
    def test_init_database(self, db_manager):
        """Test database initialization"""
        # Check if tables were created
        import sqlite3
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['pages', 'search_history', 'search_cache', 'page_links']
        for table in expected_tables:
            assert table in tables
        
        conn.close()
    
    def test_store_pages(self, db_manager, sample_crawl_results):
        """Test storing crawl results in database"""
        db_manager.store_pages(sample_crawl_results)
        
        # Check if pages were stored
        import sqlite3
        conn = sqlite3.connect(db_manager.db_path)
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
    
    def test_get_all_pages(self, db_manager, sample_crawl_results):
        """Test retrieving all pages from database"""
        db_manager.store_pages(sample_crawl_results)
        
        pages = db_manager.get_all_pages()
        
        assert len(pages) == len(sample_crawl_results)
        assert pages[0]['url'] == sample_crawl_results[0].url
        assert pages[0]['title'] == sample_crawl_results[0].title
    
    def test_get_page_by_url(self, db_manager, sample_crawl_results):
        """Test retrieving page by URL"""
        db_manager.store_pages(sample_crawl_results)
        
        page = db_manager.get_page_by_url("https://example.com/page1")
        
        assert page is not None
        assert page['url'] == "https://example.com/page1"
        assert page['title'] == "Python Programming Tutorial"
    
    def test_get_page_route(self, db_manager, sample_crawl_results):
        """Test page route tracking"""
        db_manager.store_pages(sample_crawl_results)
        
        # Get route for the deepest page
        import sqlite3
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM pages WHERE url = ?", ("https://example.com/page3",))
        page_id = cursor.fetchone()[0]
        conn.close()
        
        route = db_manager.get_page_route(page_id)
        
        assert len(route) == 3  # Should have 3 pages in route
        assert route[0]["url"] == "https://example.com/page1"
        assert route[1]["url"] == "https://example.com/page2"
        assert route[2]["url"] == "https://example.com/page3"
    
    def test_cache_operations(self, db_manager):
        """Test cache operations"""
        query = "test query"
        results = [{"url": "https://example.com", "title": "Test"}]
        
        # Cache results
        db_manager.cache_results(query, results)
        
        # Retrieve cached results
        cached = db_manager.get_cached_results(query)
        
        assert cached is not None
        assert len(cached) == 1
        assert cached[0]["url"] == "https://example.com"
    
    def test_search_history(self, db_manager):
        """Test search history operations"""
        # Record some searches
        db_manager.record_search("python", 5, 100.0, False)
        db_manager.record_search("web development", 3, 150.0, True)
        
        # Get history
        history = db_manager.get_search_history()
        
        assert len(history) >= 2
        assert any(h["query"] == "python" for h in history)
        assert any(h["query"] == "web development" for h in history)
    
    def test_get_stats(self, db_manager, sample_crawl_results):
        """Test statistics retrieval"""
        db_manager.store_pages(sample_crawl_results)
        db_manager.record_search("test", 1, 50.0, False)
        
        stats = db_manager.get_stats()
        
        assert "total_pages" in stats
        assert "total_searches" in stats
        assert "cached_queries" in stats
        assert "database_size" in stats
        
        assert stats["total_pages"] == len(sample_crawl_results)
        assert stats["total_searches"] >= 1

class TestTFIDFIndexer:
    
    def test_clean_text(self, tfidf_indexer):
        """Test text cleaning function"""
        text = "  Hello, World!  This is a TEST.  "
        cleaned = tfidf_indexer.clean_text(text)
        
        assert cleaned == "hello world this is a test"
        assert "," not in cleaned
        assert "!" not in cleaned
        assert "." not in cleaned
    
    def test_build_index(self, tfidf_indexer):
        """Test building TF-IDF index"""
        documents = [
            {"title": "Python Tutorial", "content": "Learn Python programming"},
            {"title": "Web Development", "content": "Build web applications"}
        ]
        
        tfidf_indexer.build_index(documents)
        
        assert tfidf_indexer.tfidf_matrix is not None
        assert len(tfidf_indexer.documents) == 2
    
    def test_search(self, tfidf_indexer):
        """Test search functionality"""
        documents = [
            {"title": "Python Tutorial", "content": "Learn Python programming language"},
            {"title": "Web Development", "content": "Build web applications with frameworks"}
        ]
        
        tfidf_indexer.build_index(documents)
        results = tfidf_indexer.search("Python programming")
        
        assert len(results) > 0
        assert results[0]["title"] == "Python Tutorial"
        assert "similarity_score" in results[0]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
