"""
Redis caching service for performance optimization
"""
import json
import pickle
import hashlib
from typing import Any, Optional, List, Dict, Union
from datetime import timedelta
import redis
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service for embeddings, search results, and other data"""
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=False,  # Keep binary for pickle data
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache service: {e}")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate a consistent cache key"""
        # Create hash of identifier for consistent key length
        hash_obj = hashlib.md5(identifier.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for Redis storage"""
        try:
            # Try JSON first for simple data types
            if isinstance(data, (dict, list, str, int, float, bool)):
                return json.dumps(data).encode()
            else:
                # Use pickle for complex objects
                return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Failed to serialize data: {e}")
            return pickle.dumps(data)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from Redis storage"""
        try:
            # Try JSON first
            return json.loads(data.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            try:
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Failed to deserialize data: {e}")
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL"""
        if not self.redis_client:
            return False
        
        try:
            serialized_value = self._serialize_data(value)
            if ttl:
                return self.redis_client.setex(key, ttl, serialized_value)
            else:
                return self.redis_client.set(key, serialized_value)
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            return self._deserialize_data(data)
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear cache pattern {pattern}: {e}")
            return 0
    
    # Embedding-specific cache methods
    def cache_embedding(self, text: str, model: str, embedding: List[float], ttl: int = 3600) -> bool:
        """Cache text embedding with 1 hour default TTL"""
        key = self._generate_key("embedding", f"{model}:{text}")
        return self.set(key, embedding, ttl)
    
    def get_cached_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding for text and model"""
        key = self._generate_key("embedding", f"{model}:{text}")
        return self.get(key)
    
    # Search result cache methods
    def cache_search_results(self, query: str, filters: Dict[str, Any], results: List[Dict], ttl: int = 1800) -> bool:
        """Cache search results with 30 minute default TTL"""
        # Create cache key from query and filters
        cache_input = f"{query}:{json.dumps(filters, sort_keys=True)}"
        key = self._generate_key("search", cache_input)
        return self.set(key, results, ttl)
    
    def get_cached_search_results(self, query: str, filters: Dict[str, Any]) -> Optional[List[Dict]]:
        """Get cached search results"""
        cache_input = f"{query}:{json.dumps(filters, sort_keys=True)}"
        key = self._generate_key("search", cache_input)
        return self.get(key)
    
    # RAG response cache methods
    def cache_rag_response(self, query: str, model: str, context_hash: str, response: Dict, ttl: int = 7200) -> bool:
        """Cache RAG response with 2 hour default TTL"""
        cache_input = f"{query}:{model}:{context_hash}"
        key = self._generate_key("rag", cache_input)
        return self.set(key, response, ttl)
    
    def get_cached_rag_response(self, query: str, model: str, context_hash: str) -> Optional[Dict]:
        """Get cached RAG response"""
        cache_input = f"{query}:{model}:{context_hash}"
        key = self._generate_key("rag", cache_input)
        return self.get(key)
    
    # Document processing cache methods
    def cache_document_chunks(self, document_id: str, chunks: List[Dict], ttl: int = 86400) -> bool:
        """Cache document chunks with 24 hour default TTL"""
        key = self._generate_key("chunks", document_id)
        return self.set(key, chunks, ttl)
    
    def get_cached_document_chunks(self, document_id: str) -> Optional[List[Dict]]:
        """Get cached document chunks"""
        key = self._generate_key("chunks", document_id)
        return self.get(key)
    
    # Performance monitoring cache methods
    def increment_counter(self, metric_name: str, amount: int = 1) -> Optional[int]:
        """Increment a performance counter"""
        if not self.redis_client:
            return None
        
        try:
            key = f"metrics:counter:{metric_name}"
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment counter {metric_name}: {e}")
            return None
    
    def set_gauge(self, metric_name: str, value: float) -> bool:
        """Set a gauge metric value"""
        if not self.redis_client:
            return False
        
        try:
            key = f"metrics:gauge:{metric_name}"
            return self.redis_client.set(key, str(value))
        except Exception as e:
            logger.error(f"Failed to set gauge {metric_name}: {e}")
            return False
    
    def get_metrics(self, pattern: str = "metrics:*") -> Dict[str, Any]:
        """Get all metrics matching pattern"""
        if not self.redis_client:
            return {}
        
        try:
            keys = self.redis_client.keys(pattern)
            metrics = {}
            for key in keys:
                value = self.redis_client.get(key)
                if value:
                    try:
                        metrics[key.decode()] = float(value.decode())
                    except ValueError:
                        metrics[key.decode()] = value.decode()
            return metrics
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Check Redis health and return status"""
        if not self.redis_client:
            return {"status": "unhealthy", "error": "Redis client not initialized"}
        
        try:
            # Test basic operations
            test_key = "health_check_test"
            self.redis_client.set(test_key, "test", ex=10)
            value = self.redis_client.get(test_key)
            self.redis_client.delete(test_key)
            
            # Get Redis info
            info = self.redis_client.info()
            
            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime": info.get("uptime_in_seconds", 0),
                "test_operation": "success" if value == b"test" else "failed"
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global cache service instance
cache_service = CacheService()