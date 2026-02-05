"""
Cache decorators for FastAPI endpoints

Provides easy-to-use decorators for caching endpoint responses.
"""
import functools
import hashlib
import json
import logging
from typing import Callable, Optional, Union
from datetime import timedelta
from fastapi import Request

logger = logging.getLogger(__name__)


def cache_key_builder(
    func_name: str,
    request: Request = None,
    **kwargs
) -> str:
    """
    Build a cache key from function name and arguments.
    
    Args:
        func_name: Name of the function
        request: FastAPI request object
        **kwargs: Additional parameters
        
    Returns:
        Cache key string
    """
    # Start with function name
    key_parts = [func_name]
    
    # Add path parameters if available
    if request:
        # Only use path, not query params to avoid cache issues
        key_parts.append(str(request.url.path))
    
    # Add additional kwargs (sorted for consistency)
    if kwargs:
        # Filter out common non-cacheable params
        cacheable_kwargs = {
            k: v for k, v in kwargs.items() 
            if k not in ['db', 'session', 'use_case'] and not k.startswith('_')
        }
        if cacheable_kwargs:
            kwargs_str = json.dumps(cacheable_kwargs, sort_keys=True, default=str)
            key_parts.append(kwargs_str)
    
    # Create hash of the key
    key_string = "|".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    cache_key = f"cache:{func_name}:{key_hash}"
    logger.debug(f"🔑 Generated cache key: {cache_key} from {key_string}")
    
    return cache_key


def cached(
    ttl: Union[int, timedelta] = 300,  # 5 minutes default
    key_prefix: Optional[str] = None
):
    """
    Decorator to cache function results in Redis.
    
    Usage:
        @cached(ttl=600)  # Cache for 10 minutes
        async def get_expensive_data(user_id: int):
            # expensive operation
            return data
    
    Args:
        ttl: Time to live in seconds or timedelta
        key_prefix: Optional prefix for cache key
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            from backend.src_v3.infrastructure.cache import get_redis_cache
            
            try:
                # Get Redis cache
                redis_cache = await get_redis_cache()
                
                # Build cache key
                func_name = key_prefix or func.__name__
                
                # Try to extract request from kwargs first, then args
                request = kwargs.get('request')
                if not request:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                
                # Remove request from kwargs for key building
                kwargs_for_key = {k: v for k, v in kwargs.items() if k != 'request'}
                
                cache_key = cache_key_builder(func_name, request=request, **kwargs_for_key)
                
                # Try to get from cache
                logger.debug(f"🔍 Checking cache for: {cache_key}")
                cached_value = await redis_cache.get(cache_key)
                
                if cached_value is not None:
                    logger.info(f"✅ Cache HIT for {func_name}")
                    return cached_value
                
                # Cache miss - call function
                logger.info(f"❌ Cache MISS for {func_name} - executing function")
                result = await func(*args, **kwargs)
                
                # Store in cache
                await redis_cache.set(cache_key, result, ttl=ttl)
                logger.info(f"💾 Cached result for {func_name} (TTL: {ttl}s)")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Cache error for {func.__name__}: {e}")
                logger.warning("⚠️  Falling back to uncached execution")
                # Fall back to normal execution if cache fails
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Decorator to invalidate cache after function execution.
    
    Usage:
        @invalidate_cache("user:*")
        async def update_user(user_id: int, data: dict):
            # update user
            return updated_user
    
    Args:
        pattern: Redis key pattern to invalidate
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            from backend.src_v3.infrastructure.cache import get_redis_cache
            
            # Execute function first
            result = await func(*args, **kwargs)
            
            try:
                # Invalidate cache after successful execution
                redis_cache = await get_redis_cache()
                deleted = await redis_cache.clear_pattern(pattern)
                logger.info(f"🗑️  Invalidated {deleted} cache entries matching: {pattern}")
            except Exception as e:
                logger.error(f"❌ Cache invalidation error: {e}")
            
            return result
        
        return wrapper
    return decorator
