"""
Redis Cache Client Implementation

Provides a comprehensive caching layer with connection pooling,
automatic serialization, and detailed logging.
"""
import json
import logging
from typing import Optional, Any, Union
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Async Redis cache implementation with comprehensive logging.
    
    Features:
    - Connection pooling
    - Automatic JSON serialization/deserialization
    - TTL support
    - Detailed logging for all operations
    - Error handling and fallback
    """
    
    def __init__(self, redis_url: str):
        """
        Initialize Redis cache client.
        
        Args:
            redis_url: Redis connection URL (e.g., redis://redis:6379/0)
        """
        self.redis_url = redis_url
        self.client: Optional[Redis] = None
        self._is_connected = False
        logger.info(f"🔧 Redis cache initialized with URL: {redis_url}")
    
    async def connect(self):
        """Establish connection to Redis server."""
        try:
            logger.info("🔌 Attempting to connect to Redis...")
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=50
            )
            
            # Test connection
            await self.client.ping()
            self._is_connected = True
            logger.info("✅ Redis connection established successfully")
            
            # Log Redis info
            info = await self.client.info()
            logger.info(f"📊 Redis version: {info.get('redis_version', 'unknown')}")
            logger.info(f"📊 Connected clients: {info.get('connected_clients', 0)}")
            logger.info(f"📊 Used memory: {info.get('used_memory_human', 'unknown')}")
            
        except ConnectionError as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self._is_connected = False
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to Redis: {e}")
            self._is_connected = False
            raise
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            logger.info("🔌 Disconnecting from Redis...")
            await self.client.close()
            self._is_connected = False
            logger.info("✅ Redis disconnected successfully")
    
    async def is_healthy(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            if not self.client:
                logger.warning("⚠️  Redis client not initialized")
                return False
            
            await self.client.ping()
            logger.debug("✅ Redis health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ Redis health check failed: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            if not self._is_connected:
                logger.warning(f"⚠️  Redis not connected, skipping GET for key: {key}")
                return None
            
            logger.debug(f"🔍 Redis GET: {key}")
            value = await self.client.get(key)
            
            if value is None:
                logger.debug(f"❌ Cache MISS: {key}")
                return None
            
            logger.info(f"✅ Cache HIT: {key}")
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return value
                
        except RedisError as e:
            logger.error(f"❌ Redis GET error for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error in GET for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds or timedelta
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._is_connected:
                logger.warning(f"⚠️  Redis not connected, skipping SET for key: {key}")
                return False
            
            # Serialize value to JSON
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            logger.debug(f"💾 Redis SET: {key} (TTL: {ttl}s)")
            
            if ttl:
                await self.client.setex(key, ttl, serialized_value)
            else:
                await self.client.set(key, serialized_value)
            
            logger.info(f"✅ Cache SET successful: {key}")
            return True
            
        except RedisError as e:
            logger.error(f"❌ Redis SET error for key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error in SET for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            if not self._is_connected:
                logger.warning(f"⚠️  Redis not connected, skipping DELETE for key: {key}")
                return False
            
            logger.debug(f"🗑️  Redis DELETE: {key}")
            result = await self.client.delete(key)
            
            if result > 0:
                logger.info(f"✅ Cache DELETE successful: {key}")
                return True
            else:
                logger.debug(f"⚠️  Key not found for DELETE: {key}")
                return False
                
        except RedisError as e:
            logger.error(f"❌ Redis DELETE error for key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error in DELETE for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if exists, False otherwise
        """
        try:
            if not self._is_connected:
                return False
            
            result = await self.client.exists(key)
            exists = result > 0
            logger.debug(f"🔍 Redis EXISTS: {key} = {exists}")
            return exists
            
        except RedisError as e:
            logger.error(f"❌ Redis EXISTS error for key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error in EXISTS for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            if not self._is_connected:
                logger.warning(f"⚠️  Redis not connected, skipping CLEAR_PATTERN: {pattern}")
                return 0
            
            logger.info(f"🗑️  Redis CLEAR_PATTERN: {pattern}")
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.client.delete(*keys)
                logger.info(f"✅ Deleted {deleted} keys matching pattern: {pattern}")
                return deleted
            else:
                logger.info(f"⚠️  No keys found matching pattern: {pattern}")
                return 0
                
        except RedisError as e:
            logger.error(f"❌ Redis CLEAR_PATTERN error for pattern {pattern}: {e}")
            return 0
        except Exception as e:
            logger.error(f"❌ Unexpected error in CLEAR_PATTERN for pattern {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> dict:
        """
        Get Redis statistics.
        
        Returns:
            Dictionary with Redis stats
        """
        try:
            if not self._is_connected:
                return {"error": "Not connected"}
            
            info = await self.client.info()
            stats = {
                "connected": self._is_connected,
                "version": info.get("redis_version"),
                "uptime_seconds": info.get("uptime_in_seconds"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "used_memory_peak_human": info.get("used_memory_peak_human"),
                "total_commands_processed": info.get("total_commands_processed"),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
            
            # Calculate hit rate
            hits = stats["keyspace_hits"]
            misses = stats["keyspace_misses"]
            total = hits + misses
            if total > 0:
                stats["hit_rate"] = f"{(hits / total * 100):.2f}%"
            else:
                stats["hit_rate"] = "N/A"
            
            logger.debug(f"📊 Redis stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting Redis stats: {e}")
            return {"error": str(e)}


# Global cache instance
_redis_cache: Optional[RedisCache] = None


async def get_redis_cache() -> RedisCache:
    """
    Get or create Redis cache instance.
    
    Returns:
        RedisCache instance
    """
    global _redis_cache
    
    if _redis_cache is None:
        from backend.src_v3.infrastructure.config.settings import get_settings
        settings = get_settings()
        _redis_cache = RedisCache(settings.REDIS_URL)
        await _redis_cache.connect()
    
    return _redis_cache
