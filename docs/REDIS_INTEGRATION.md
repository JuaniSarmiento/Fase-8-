# Redis Integration Guide

## Overview

Redis has been fully integrated into the AI-Native MVP V3 project for caching and performance optimization.

## 🚀 Features

- **Automatic Connection Management**: Redis connects on startup and disconnects on shutdown
- **Health Checks**: Built-in health monitoring with detailed metrics
- **Comprehensive Logging**: All Redis operations are logged with emoji indicators
- **Connection Pooling**: Optimized with up to 50 concurrent connections
- **Automatic Serialization**: JSON encoding/decoding handled automatically
- **TTL Support**: Set expiration times for cached values
- **Pattern Matching**: Clear multiple cache keys at once
- **Error Handling**: Graceful fallback if Redis is unavailable

## 🏗️ Architecture

```
backend/src_v3/infrastructure/cache/
├── __init__.py           # Module exports
├── redis_client.py       # Core Redis client implementation
└── decorators.py         # Cache decorators for endpoints
```

## 📝 Configuration

### Environment Variables

```bash
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_RETRY_ON_TIMEOUT=True
```

### Docker Compose

Redis runs as a service with:
- Persistent storage
- Health checks
- Memory limits (256MB)
- LRU eviction policy
- Appendonly persistence

## 🔧 Usage

### 1. Basic Cache Operations

```python
from backend.src_v3.infrastructure.cache import get_redis_cache

# Get Redis instance
redis_cache = await get_redis_cache()

# Set value (with TTL)
await redis_cache.set("user:123", {"name": "John"}, ttl=300)

# Get value
user = await redis_cache.get("user:123")

# Delete value
await redis_cache.delete("user:123")

# Check if exists
exists = await redis_cache.exists("user:123")

# Clear by pattern
deleted = await redis_cache.clear_pattern("user:*")
```

### 2. Cache Decorator

Use the `@cached` decorator to automatically cache endpoint responses:

```python
from fastapi import APIRouter, Request
from backend.src_v3.infrastructure.cache.decorators import cached

router = APIRouter()

@router.get("/expensive-operation")
@cached(ttl=300)  # Cache for 5 minutes
async def expensive_operation(request: Request, param: str):
    # This will only execute on cache miss
    result = await do_expensive_work(param)
    return result
```

### 3. Cache Invalidation

Use the `@invalidate_cache` decorator to clear cache after mutations:

```python
from backend.src_v3.infrastructure.cache.decorators import invalidate_cache

@router.post("/users/{user_id}")
@invalidate_cache("user:*")  # Clear all user cache
async def update_user(user_id: str, data: dict):
    # Update user
    # Cache will be cleared after successful execution
    return updated_user
```

## 📊 Monitoring

### Health Check Endpoint

```bash
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

### Detailed Health Check

```bash
GET /api/v3/system/health/detailed
```

Returns:
```json
{
  "status": "healthy",
  "components": {
    "redis": {
      "status": "healthy",
      "connected_clients": 2,
      "used_memory": "1.2M",
      "hit_rate": "85.3%"
    }
  }
}
```

### Redis Statistics

```bash
GET /api/v3/system/redis/stats
```

Returns detailed Redis metrics:
- Version
- Uptime
- Connected clients
- Memory usage
- Commands processed
- Hit rate

### Test Redis Connection

```bash
POST /api/v3/system/redis/test
```

Tests Redis operations (set, get, delete) and returns results.

## 📈 Cached Endpoints

The following endpoints are cached:

| Endpoint | Cache Duration | Key Prefix |
|----------|----------------|------------|
| `/api/v3/system/stats` | 30 seconds | `system_stats` |
| `/api/v3/analytics/courses/{id}` | 60 seconds | `course_analytics` |
| `/api/v3/analytics/students/{id}` | 45 seconds | `student_risk` |

## 🔍 Logging

All Redis operations are logged with descriptive emojis:

- 🔧 Configuration/Initialization
- 🔌 Connection events
- ✅ Successful operations
- ❌ Errors and failures
- 🔍 Cache lookups
- 💾 Cache writes
- 🗑️  Cache deletions
- 📊 Statistics
- ⚠️  Warnings

### Example Logs

```
2026-02-05 10:00:00 - INFO - 🔧 Redis cache initialized with URL: redis://redis:6379/0
2026-02-05 10:00:01 - INFO - 🔌 Attempting to connect to Redis...
2026-02-05 10:00:01 - INFO - ✅ Redis connection established successfully
2026-02-05 10:00:01 - INFO - 📊 Redis version: 7.2.4
2026-02-05 10:00:05 - INFO - ✅ Cache HIT: cache:system_stats:a3f2c1
2026-02-05 10:01:00 - INFO - ❌ Cache MISS: cache:course_analytics:b4e3d2 - executing function
2026-02-05 10:01:02 - INFO - 💾 Cached result for course_analytics (TTL: 60s)
```

## 🐛 Troubleshooting

### Redis Not Connecting

Check if Redis container is running:
```bash
docker-compose ps redis
```

View Redis logs:
```bash
docker-compose logs redis
```

### Clear All Cache

Connect to Redis and flush:
```bash
docker-compose exec redis redis-cli
> FLUSHALL
```

### Memory Issues

Check memory usage:
```bash
docker-compose exec redis redis-cli INFO memory
```

Redis is configured with:
- Max memory: 256MB
- Eviction policy: allkeys-lru (least recently used)

## 🚢 Deployment

### Production Configuration

Update `docker-compose.production.yml` with Redis service (already done).

Set production environment variables:
```bash
REDIS_URL=redis://redis:6379/0
```

### Scaling Redis

For production, consider:
- Redis Cluster for high availability
- Redis Sentinel for automatic failover
- Persistent volume for data durability
- Monitoring with Redis metrics

## 🔐 Security

Current setup is for development. For production:

1. **Enable Authentication**:
   ```bash
   command: redis-server --requirepass yourpassword
   ```

2. **Update Connection URL**:
   ```bash
   REDIS_URL=redis://:yourpassword@redis:6379/0
   ```

3. **Use TLS** for encrypted connections

4. **Restrict Network Access** to Redis port

## 📚 Additional Resources

- [Redis Documentation](https://redis.io/documentation)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [FastAPI Caching Guide](https://fastapi.tiangolo.com/advanced/caching/)

## ✅ Testing

Run Redis tests:
```bash
# Via API endpoint
curl -X POST http://localhost:8000/api/v3/system/redis/test

# View Redis keys
docker-compose exec redis redis-cli KEYS '*'

# Monitor Redis commands
docker-compose exec redis redis-cli MONITOR
```
