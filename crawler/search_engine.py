import sqlite3
import json
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging
import re

class SearchEngine:
    def __init__(self, db_path: str, cache_ttl: int = 3600):
        self.db_path = db_path
        self.cache_ttl = cache_ttl
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=10000,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        self.tfidf_matrix = None
        self.documents = []
        self.logger = logging.getLogger(__name__)
        
        self.init_database()
        self.load_index()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Pages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                crawl_time TIMESTAMP NOT NULL,
                depth INTEGER NOT NULL,
                parent_url TEXT,
                status_code INTEGER DEFAULT 200,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                results_count INTEGER NOT NULL,
                execution_time REAL NOT NULL,
                cached BOOLEAN DEFAULT FALSE,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE NOT NULL,
                query TEXT NOT NULL,
                results TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        ''')
        
        # Links table for route tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS page_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_page_id INTEGER NOT NULL,
                to_page_id INTEGER NOT NULL,
                link_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_page_id) REFERENCES pages (id),
                FOREIGN KEY (to_page_id) REFERENCES pages (id),
                UNIQUE(from_page_id, to_page_id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pages_crawl_time ON pages(crawl_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_hash ON search_cache(query_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires ON search_cache(expires_at)')
        
        conn.commit()
        conn.close()
    
    def clean_text(self, text: str) -> str:
        """Clean and preprocess text for indexing"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters but keep alphanumeric and spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Convert to lowercase
        text = text.lower()
        
        return text
    
    def store_pages(self, crawl_results: List) -> None:
        """Store crawl results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for result in crawl_results:
                # Insert or update page
                cursor.execute('''
                    INSERT OR REPLACE INTO pages 
                    (url, title, content, crawl_time, depth, parent_url, status_code, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    result.url,
                    result.title,
                    result.content,
                    result.crawl_time.isoformat(),
                    result.depth,
                    result.parent_url,
                    result.status_code
                ))
                
                page_id = cursor.lastrowid
                
                # Store links for route tracking
                if result.parent_url:
                    cursor.execute('SELECT id FROM pages WHERE url = ?', (result.parent_url,))
                    parent_row = cursor.fetchone()
                    if parent_row:
                        parent_id = parent_row[0]
                        cursor.execute('''
                            INSERT OR IGNORE INTO page_links (from_page_id, to_page_id)
                            VALUES (?, ?)
                        ''', (parent_id, page_id))
            
            conn.commit()
            self.logger.info(f"Stored {len(crawl_results)} pages in database")
            
            # Rebuild search index
            self.load_index()
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error storing pages: {e}")
            raise
        finally:
            conn.close()
    
    def load_index(self) -> None:
        """Load documents and build TF-IDF index"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, url, title, content FROM pages ORDER BY id')
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            self.documents = []
            self.tfidf_matrix = None
            return
        
        # Prepare documents for indexing
        self.documents = []
        texts = []
        
        for row in rows:
            page_id, url, title, content = row
            
            # Combine title and content with title weighted more
            combined_text = f"{title} {title} {content}"  # Title appears twice for higher weight
            cleaned_text = self.clean_text(combined_text)
            
            self.documents.append({
                'id': page_id,
                'url': url,
                'title': title,
                'content': content
            })
            texts.append(cleaned_text)
        
        # Build TF-IDF matrix
        if texts:
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            self.logger.info(f"Built search index with {len(texts)} documents")
    
    def get_page_route(self, page_id: int) -> List[Dict[str, str]]:
        """Get the route/path to a page from root"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        route = []
        current_id = page_id
        visited = set()
        
        while current_id and current_id not in visited:
            visited.add(current_id)
            
            # Get current page info
            cursor.execute('SELECT url, title, parent_url FROM pages WHERE id = ?', (current_id,))
            row = cursor.fetchone()
            
            if not row:
                break
            
            url, title, parent_url = row
            route.insert(0, {'url': url, 'title': title})
            
            # Find parent page ID
            if parent_url:
                cursor.execute('SELECT id FROM pages WHERE url = ?', (parent_url,))
                parent_row = cursor.fetchone()
                current_id = parent_row[0] if parent_row else None
            else:
                current_id = None
        
        conn.close()
        return route
    
    def get_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get_cached_results(self, query: str) -> Optional[List[Dict]]:
        """Get cached search results if available and not expired"""
        cache_key = self.get_cache_key(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT results FROM search_cache 
            WHERE query_hash = ? AND expires_at > CURRENT_TIMESTAMP
        ''', (cache_key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def cache_results(self, query: str, results: List[Dict]) -> None:
        """Cache search results"""
        cache_key = self.get_cache_key(query)
        expires_at = datetime.now() + timedelta(seconds=self.cache_ttl)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO search_cache (query_hash, query, results, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (cache_key, query, json.dumps(results), expires_at.isoformat()))
        
        conn.commit()
        conn.close()
    
    def clean_expired_cache(self) -> None:
        """Remove expired cache entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM search_cache WHERE expires_at <= CURRENT_TIMESTAMP')
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted > 0:
            self.logger.info(f"Cleaned {deleted} expired cache entries")
    
    def search(self, query: str, limit: int = 10, use_cache: bool = True) -> Dict:
        """Search for pages matching the query"""
        start_time = datetime.now()
        
        # Clean expired cache entries periodically
        self.clean_expired_cache()
        
        # Check cache first
        cached_results = None
        if use_cache:
            cached_results = self.get_cached_results(query)
            if cached_results:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Record search in history
                self.record_search(query, len(cached_results), execution_time, cached=True)
                
                return {
                    'results': cached_results[:limit],
                    'total_found': len(cached_results),
                    'execution_time_ms': execution_time,
                    'cached': True
                }
        
        # Perform search
        if not self.documents or self.tfidf_matrix is None:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.record_search(query, 0, execution_time, cached=False)
            return {
                'results': [],
                'total_found': 0,
                'execution_time_ms': execution_time,
                'cached': False
            }
        
        # Clean and vectorize query
        cleaned_query = self.clean_text(query)
        query_vector = self.vectorizer.transform([cleaned_query])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Get top results
        top_indices = np.argsort(similarity_scores)[::-1]
        
        results = []
        for idx in top_indices:
            score = similarity_scores[idx]
            
            # Only include results with meaningful similarity
            if score > 0.01:  # Minimum threshold
                doc = self.documents[idx]
                
                # Create content snippet
                content = doc['content']
                snippet_length = 200
                snippet = content[:snippet_length]
                if len(content) > snippet_length:
                    snippet += "..."
                
                # Get page route
                route = self.get_page_route(doc['id'])
                
                # Get last crawled time
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT crawl_time FROM pages WHERE id = ?', (doc['id'],))
                crawl_time_row = cursor.fetchone()
                conn.close()
                
                last_crawled = crawl_time_row[0] if crawl_time_row else datetime.now().isoformat()
                
                results.append({
                    'url': doc['url'],
                    'title': doc['title'],
                    'content_snippet': snippet,
                    'similarity_score': float(score),
                    'route': route,
                    'last_crawled': last_crawled
                })
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Cache results if there are any
        if results and use_cache:
            self.cache_results(query, results)
        
        # Record search in history
        self.record_search(query, len(results), execution_time, cached=False)
        
        return {
            'results': results[:limit],
            'total_found': len(results),
            'execution_time_ms': execution_time,
            'cached': False
        }
    
    def record_search(self, query: str, results_count: int, execution_time: float, cached: bool = False) -> None:
        """Record search in history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_history (query, results_count, execution_time, cached)
            VALUES (?, ?, ?, ?)
        ''', (query, results_count, execution_time, cached))
        
        conn.commit()
        conn.close()
    
    def get_search_history(self, limit: int = 50) -> List[Dict]:
        """Get recent search history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT query, results_count, execution_time, cached, searched_at
            FROM search_history
            ORDER BY searched_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            query, results_count, execution_time, cached, searched_at = row
            history.append({
                'query': query,
                'results_count': results_count,
                'execution_time': execution_time,
                'cached': bool(cached),
                'searched_at': searched_at
            })
        
        return history
    
    def get_stats(self) -> Dict:
        """Get search engine statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total pages
        cursor.execute('SELECT COUNT(*) FROM pages')
        total_pages = cursor.fetchone()[0]
        
        # Total searches
        cursor.execute('SELECT COUNT(*) FROM search_history')
        total_searches = cursor.fetchone()[0]
        
        # Cached queries
        cursor.execute('SELECT COUNT(*) FROM search_cache WHERE expires_at > CURRENT_TIMESTAMP')
        cached_queries = cursor.fetchone()[0]
        
        # Last crawl time
        cursor.execute('SELECT MAX(crawl_time) FROM pages')
        last_crawl = cursor.fetchone()[0]
        
        # Database size estimation
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size_bytes = cursor.fetchone()[0] or 0
        db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
        
        # Index size (number of unique terms)
        index_size = len(self.vectorizer.vocabulary_) if hasattr(self.vectorizer, 'vocabulary_') else 0
        
        conn.close()
        
        return {
            'total_pages': total_pages,
            'total_searches': total_searches,
            'cached_queries': cached_queries,
            'last_crawl': last_crawl,
            'database_size': f"{db_size_mb} MB",
            'index_size': index_size,
            'crawl_status': 'idle'  # This will be updated by the main application
        }
    
    def clear_cache(self) -> int:
        """Clear all cached search results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM search_cache')
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Cleared {deleted} cache entries")
        return deleted
