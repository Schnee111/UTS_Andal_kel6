import os
import json
from typing import List, Dict, Any
from pathlib import Path

class Config:
    """Global configuration management for the search engine"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or set defaults"""
        default_config = {
            "seed_urls": [
                "https://www.upi.edu",
                "https://fpmipa.upi.edu"
            ],
            "max_pages": 100,
            "max_depth": 3,
            "crawl_delay": 1.0,
            "crawl_algorithm": "BFS",  # BFS or DFS
            "user_agent": "InternalSearchBot/1.0 (Educational Purpose)",
            "allowed_domains": [
                "upi.edu",
                "fpmipa.upi.edu"
            ],
            "cache_enabled": True,
            "cache_ttl": 3600,  # 1 hour in seconds
            "database_path": "database/search_index.db",
            "max_concurrent_requests": 10,
            "request_timeout": 30,
            "retry_attempts": 3,
            "respect_robots_txt": True,
            "extract_images": False,
            "extract_documents": True,
            "content_types": [
                "text/html",
                "text/plain"
            ],
            "exclude_patterns": [
                "*.pdf",
                "*.doc*",
                "*.ppt*",
                "*.xls*",
                "/admin/",
                "/login/",
                "/logout/"
            ]
        }
            
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                # Merge with defaults
                default_config.update(file_config)
            except Exception as e:
                print(f"Error loading config file: {e}. Using defaults.")
        
        # Set attributes
        for key, value in default_config.items():
            setattr(self, key.upper(), value)
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.DATABASE_PATH), exist_ok=True)
        
        # Save current config
        self.save_config()
    
    def save_config(self):
        """Save current configuration to file"""
        config_data = {}
        for attr_name in dir(self):
            if attr_name.isupper() and not attr_name.startswith('_'):
                config_data[attr_name.lower()] = getattr(self, attr_name)
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        for key, value in updates.items():
            if hasattr(self, key.upper()):
                setattr(self, key.upper(), value)
        
        self.save_config()
    
    def get_crawler_config(self) -> Dict[str, Any]:
        """Get configuration dict for crawler"""
        return {
            'seed_urls': self.SEED_URLS,
            'max_pages': self.MAX_PAGES,
            'max_depth': self.MAX_DEPTH,
            'crawl_delay': self.CRAWL_DELAY,
            'user_agent': self.USER_AGENT,
            'allowed_domains': self.ALLOWED_DOMAINS,
            'max_concurrent_requests': self.MAX_CONCURRENT_REQUESTS,
            'request_timeout': self.REQUEST_TIMEOUT,
            'retry_attempts': self.RETRY_ATTEMPTS,
            'respect_robots_txt': self.RESPECT_ROBOTS_TXT,
            'content_types': self.CONTENT_TYPES,
            'exclude_patterns': self.EXCLUDE_PATTERNS
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as dict"""
        config_data = {}
        for attr_name in dir(self):
            if attr_name.isupper() and not attr_name.startswith('_'):
                config_data[attr_name.lower()] = getattr(self, attr_name)
        return config_data
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        self.load_config()
