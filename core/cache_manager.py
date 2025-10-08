"""Cache Graph + Subgraph Implementation — Intelligent data caching with TTL management."""

import json
import logging
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
import time
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CacheNode:
    """
    Cache node structure for storing fetched data with metadata.
    
    Attributes:
        key: Unique cache key
        prompt: Original query/prompt
        lunarcrush_data: LunarCrush sentiment and coin data
        polymarket_data: Polymarket events and market data
        derived_data: Computed/derived signals and analysis
        ttl_seconds: Time to live in seconds
        timestamp: When the cache entry was created
        expires_at: When the cache entry expires
    """
    key: str
    prompt: str
    lunarcrush_data: Optional[Dict[str, Any]] = None
    polymarket_data: Optional[Dict[str, Any]] = None
    derived_data: Optional[Dict[str, Any]] = None
    ttl_seconds: int = 300  # 5 minutes default
    timestamp: str = ""
    expires_at: str = ""
    
    def __post_init__(self):
        """Set timestamp and expiry after initialization."""
        if not self.timestamp:
            now = datetime.now()
            self.timestamp = now.isoformat()
            self.expires_at = (now + timedelta(seconds=self.ttl_seconds)).isoformat()
    
    def is_expired(self) -> bool:
        """Check if cache node has expired."""
        now = datetime.now()
        expires = datetime.fromisoformat(self.expires_at)
        return now > expires
    
    def time_until_expiry(self) -> float:
        """Get seconds until expiry (negative if already expired)."""
        now = datetime.now()
        expires = datetime.fromisoformat(self.expires_at)
        return (expires - now).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cache node to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheNode':
        """Create cache node from dictionary."""
        return cls(**data)

class MCPCacheManager:
    """
    Intelligent cache manager for MCP data with subgraph support.
    
    Features:
    - TTL-based expiration
    - Intelligent key generation
    - Memory and optional persistent storage
    - Cache hit/miss tracking
    - Automatic cleanup of expired entries
    """
    
    def __init__(self, default_ttl: int = 300, max_cache_size: int = 1000, 
                 persistent_file: str = "cache_data.json"):
        """
        Initialize cache manager.
        
        Args:
            default_ttl: Default time to live in seconds
            max_cache_size: Maximum number of cache entries
            persistent_file: JSON file to persist cache data
        """
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        self.persistent_file = Path(persistent_file)
        
        # In-memory cache storage
        self.cache: Dict[str, CacheNode] = {}
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0,
            "cache_size": 0
        }
        
        # Load existing cache from file
        self._load_from_file()
        
        logger.info(f"MCPCacheManager initialized: TTL={default_ttl}s, Max size={max_cache_size}, File={persistent_file}")
        logger.info(f"📂 Loaded {len(self.cache)} cache entries from persistent storage")
    
    def generate_cache_key(self, prompt: str, data_types: List[str] = None, **kwargs) -> str:
        """
        Generate a unique cache key for the given parameters.
        
        Args:
            prompt: The original query/prompt
            data_types: Types of data requested (e.g., ['lunarcrush', 'polymarket'])
            **kwargs: Additional parameters that affect the result
            
        Returns:
            Unique cache key string
        """
        # Normalize prompt
        prompt_normalized = prompt.lower().strip()
        
        # Include data types
        types_str = ",".join(sorted(data_types or []))
        
        # Include relevant kwargs
        kwargs_str = ",".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
        
        # Create composite string
        composite = f"{prompt_normalized}|{types_str}|{kwargs_str}"
        
        # Generate hash
        cache_key = hashlib.md5(composite.encode()).hexdigest()[:16]
        
        logger.debug(f"Generated cache key: {cache_key} for prompt: '{prompt[:50]}...'")
        return cache_key
    
    def get(self, cache_key: str) -> Optional[CacheNode]:
        """
        Get cache entry by key.
        
        Args:
            cache_key: Cache key to lookup
            
        Returns:
            Cache node if found and not expired, None otherwise
        """
        self.stats["total_requests"] += 1
        
        if cache_key not in self.cache:
            self.stats["misses"] += 1
            logger.debug(f"Cache MISS: {cache_key}")
            return None
        
        node = self.cache[cache_key]
        
        # Check if expired
        if node.is_expired():
            logger.info(f"Cache entry expired: {cache_key} (expired {-node.time_until_expiry():.1f}s ago)")
            self._remove(cache_key)
            self.stats["misses"] += 1
            return None
        
        # Cache hit
        self.stats["hits"] += 1
        logger.info(f"🎯 Cache HIT: {cache_key} (expires in {node.time_until_expiry():.1f}s)")
        return node
    
    def put(self, cache_key: str, node: CacheNode) -> bool:
        """
        Store cache entry.
        
        Args:
            cache_key: Cache key
            node: Cache node to store
            
        Returns:
            True if successfully stored
        """
        # Check cache size limit
        if len(self.cache) >= self.max_cache_size and cache_key not in self.cache:
            self._evict_oldest()
        
        self.cache[cache_key] = node
        self.stats["cache_size"] = len(self.cache)
        
        logger.info(f"💾 Cache STORE: {cache_key} (TTL: {node.ttl_seconds}s)")
        
        # Save to persistent file
        self._save_to_file()
        
        return True
    
    def create_and_store(self, prompt: str, ttl_seconds: Optional[int] = None, **data) -> str:
        """
        Create a cache node and store it.
        
        Args:
            prompt: Original query/prompt
            ttl_seconds: Override default TTL
            **data: Data to store (lunarcrush_data, polymarket_data, derived_data)
            
        Returns:
            Cache key of stored entry
        """
        # Generate cache key
        data_types = [k.replace("_data", "") for k in data.keys() if k.endswith("_data")]
        cache_key = self.generate_cache_key(prompt, data_types)
        
        # Create cache node
        node = CacheNode(
            key=cache_key,
            prompt=prompt,
            ttl_seconds=ttl_seconds or self.default_ttl,
            **data
        )
        
        # Store in cache
        self.put(cache_key, node)
        return cache_key
    
    def get_or_create_key(self, prompt: str, data_types: List[str] = None, **kwargs) -> str:
        """
        Get cache key for given parameters, creating if needed.
        
        Args:
            prompt: Query/prompt
            data_types: Types of data
            **kwargs: Additional parameters
            
        Returns:
            Cache key
        """
        return self.generate_cache_key(prompt, data_types, **kwargs)
    
    def _remove(self, cache_key: str) -> bool:
        """Remove cache entry."""
        if cache_key in self.cache:
            del self.cache[cache_key]
            self.stats["cache_size"] = len(self.cache)
            return True
        return False
    
    def _evict_oldest(self) -> bool:
        """Evict oldest cache entry."""
        if not self.cache:
            return False
        
        # Find oldest entry
        oldest_key = min(self.cache.keys(), 
                        key=lambda k: self.cache[k].timestamp)
        
        logger.info(f"Cache evicting oldest entry: {oldest_key}")
        self._remove(oldest_key)
        self.stats["evictions"] += 1
        return True
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [key for key, node in self.cache.items() if node.is_expired()]
        
        for key in expired_keys:
            self._remove(key)
        
        if expired_keys:
            logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["total_requests"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate_percent": round(hit_rate, 2),
            "active_entries": len(self.cache),
            "expired_entries": sum(1 for node in self.cache.values() if node.is_expired())
        }
    
    def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        count = len(self.cache)
        self.cache.clear()
        self.stats["cache_size"] = 0
        logger.info(f"Cache cleared: {count} entries removed")
        return count
    
    def list_entries(self, include_expired: bool = False) -> List[Dict[str, Any]]:
        """
        List cache entries with metadata.
        
        Args:
            include_expired: Whether to include expired entries
            
        Returns:
            List of cache entry summaries
        """
        entries = []
        
        for key, node in self.cache.items():
            if not include_expired and node.is_expired():
                continue
            
            entry_info = {
                "key": key,
                "prompt": node.prompt[:50] + "..." if len(node.prompt) > 50 else node.prompt,
                "data_types": [k for k in ["lunarcrush_data", "polymarket_data", "derived_data"] 
                             if getattr(node, k) is not None],
                "ttl_seconds": node.ttl_seconds,
                "created": node.timestamp,
                "expires": node.expires_at,
                "expired": node.is_expired(),
                "time_until_expiry": round(node.time_until_expiry(), 1)
            }
            entries.append(entry_info)
        
        return entries
    
    def _load_from_file(self):
        """Load cache data from persistent JSON file."""
        if not self.persistent_file.exists():
            logger.debug(f"Cache file {self.persistent_file} does not exist, starting with empty cache")
            return
        
        try:
            with open(self.persistent_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Reconstruct cache nodes from JSON data
            loaded_count = 0
            expired_count = 0
            
            for key, node_data in cache_data.items():
                # Create cache node from saved data
                node = CacheNode(
                    key=node_data.get('key', key),
                    prompt=node_data.get('prompt', ''),
                    lunarcrush_data=node_data.get('lunarcrush_data'),
                    polymarket_data=node_data.get('polymarket_data'),
                    derived_data=node_data.get('derived_data'),
                    ttl_seconds=node_data.get('ttl_seconds', self.default_ttl),
                    timestamp=node_data.get('timestamp', ''),
                    expires_at=node_data.get('expires_at', '')
                )
                
                # Only load non-expired entries
                if not node.is_expired():
                    self.cache[key] = node
                    loaded_count += 1
                else:
                    expired_count += 1
            
            logger.info(f"💾 Loaded {loaded_count} valid cache entries, skipped {expired_count} expired entries")
            
        except Exception as e:
            logger.error(f"Failed to load cache from {self.persistent_file}: {e}")
    
    def _save_to_file(self):
        """Save current cache to persistent JSON file."""
        try:
            # Convert cache nodes to JSON-serializable format
            cache_data = {}
            
            for key, node in self.cache.items():
                # Skip expired entries
                if node.is_expired():
                    continue
                
                cache_data[key] = {
                    'key': node.key,
                    'prompt': node.prompt,
                    'lunarcrush_data': node.lunarcrush_data,
                    'polymarket_data': node.polymarket_data,
                    'derived_data': node.derived_data,
                    'ttl_seconds': node.ttl_seconds,
                    'timestamp': node.timestamp,
                    'expires_at': node.expires_at
                }
            
            # Write to file with proper formatting
            with open(self.persistent_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Saved {len(cache_data)} cache entries to {self.persistent_file}")
            
        except Exception as e:
            logger.error(f"Failed to save cache to {self.persistent_file}: {e}")
    
    def shutdown(self):
        """Save cache and cleanup before shutdown."""
        logger.info("🔄 Shutting down cache manager, saving to persistent storage...")
        self._save_to_file()
        self.cache.clear()

# Global cache manager instance
cache_manager = MCPCacheManager(default_ttl=300, max_cache_size=1000)