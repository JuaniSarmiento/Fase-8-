# Redis Quick Commands Reference

## 🚀 Starting Services

```bash
# Start all services (including Redis)
docker-compose up -d

# Start only Redis
docker-compose up -d redis

# Restart Redis
docker-compose restart redis
```

## 📊 Monitoring

### Check Redis Status
```bash
# Check if Redis is running
docker-compose ps redis

# Check Redis health
docker exec -it ai_native_redis redis-cli ping
# Expected output: PONG

# View Redis logs
docker-compose logs redis -f

# View backend logs with Redis operations
docker-compose logs backend -f | grep -E "Redis|Cache|HIT|MISS"
```

### Redis Statistics via API
```bash
# Get Redis stats
curl http://localhost:8000/api/v3/system/redis/stats

# Test Redis connection
curl -X POST http://localhost:8000/api/v3/system/redis/test

# Full health check
curl http://localhost:8000/api/v3/system/health/detailed
```

### Direct Redis Commands
```bash
# Connect to Redis CLI
docker exec -it ai_native_redis redis-cli

# Inside Redis CLI:
> PING                    # Test connection
> INFO                    # Get server info
> DBSIZE                  # Number of keys
> KEYS *                  # List all keys (dev only!)
> GET cache:system_stats:* # Get specific key
> TTL cache:system_stats:* # Check TTL
> FLUSHALL                # Clear all data (dev only!)
> MONITOR                 # Watch commands in real-time
```

## 🧪 Testing

### Test Cache Performance
```bash
# PowerShell
Write-Host "First call (MISS):"; 
Measure-Command { curl http://localhost:8000/api/v3/system/stats -UseBasicParsing | Out-Null }

Write-Host "Second call (HIT):"; 
Measure-Command { curl http://localhost:8000/api/v3/system/stats -UseBasicParsing | Out-Null }
```

```bash
# Bash/Linux
echo "First call (MISS):"
time curl http://localhost:8000/api/v3/system/stats

echo "Second call (HIT):"
time curl http://localhost:8000/api/v3/system/stats
```

### Verify Cache Keys
```bash
# List all cache keys
docker exec -it ai_native_redis redis-cli KEYS "cache:*"

# Get cache hit/miss stats
curl http://localhost:8000/api/v3/system/redis/stats | jq '.redis_stats | {hit_rate, keyspace_hits, keyspace_misses}'
```

## 🛠️ Maintenance

### Clear Cache
```bash
# Clear all cache
docker exec -it ai_native_redis redis-cli FLUSHALL

# Clear specific pattern
docker exec -it ai_native_redis redis-cli --eval "return redis.call('del', unpack(redis.call('keys', 'cache:system_*')))"
```

### Backup Redis Data
```bash
# Create snapshot
docker exec ai_native_redis redis-cli BGSAVE

# Copy RDB file
docker cp ai_native_redis:/data/dump.rdb ./backup/redis-backup-$(date +%Y%m%d).rdb
```

### Check Memory Usage
```bash
# Memory info
docker exec -it ai_native_redis redis-cli INFO memory

# Top keys by memory
docker exec -it ai_native_redis redis-cli --bigkeys
```

## 🐛 Debugging

### Connection Issues
```bash
# Check if Redis port is listening
docker-compose ps redis
netstat -an | grep 6379

# Test connection from host
telnet localhost 6379

# Check Redis logs for errors
docker-compose logs redis --tail=50
```

### Performance Issues
```bash
# Check slow queries
docker exec -it ai_native_redis redis-cli SLOWLOG GET 10

# Monitor commands in real-time
docker exec -it ai_native_redis redis-cli MONITOR

# Check latency
docker exec -it ai_native_redis redis-cli --latency
```

### Cache Not Working
```bash
# Verify backend can connect to Redis
curl http://localhost:8000/api/v3/system/health/detailed

# Check backend logs
docker-compose logs backend --tail=50 | grep -i redis

# Restart backend
docker-compose restart backend
```

## 📈 Production Commands

### With Password Authentication
```bash
# Connect with password
docker exec -it ai_native_redis redis-cli -a YOUR_PASSWORD

# Test with auth
docker exec -it ai_native_redis redis-cli --no-auth-warning -a YOUR_PASSWORD ping
```

### Performance Tuning
```bash
# Check current config
docker exec -it ai_native_redis redis-cli CONFIG GET maxmemory

# Set max memory (runtime)
docker exec -it ai_native_redis redis-cli CONFIG SET maxmemory 512mb

# Set eviction policy
docker exec -it ai_native_redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## 🔍 Useful Queries

### Get All Statistics
```bash
# Comprehensive Redis info
docker exec -it ai_native_redis redis-cli INFO all > redis-info.txt

# Parse specific sections
docker exec -it ai_native_redis redis-cli INFO server
docker exec -it ai_native_redis redis-cli INFO stats
docker exec -it ai_native_redis redis-cli INFO memory
docker exec -it ai_native_redis redis-cli INFO persistence
```

### Count Keys by Pattern
```bash
# Count cache keys
docker exec -it ai_native_redis redis-cli --scan --pattern 'cache:*' | wc -l

# Count all keys
docker exec -it ai_native_redis redis-cli DBSIZE
```

## 📊 Monitoring Dashboard

### One-Line Status Check
```bash
docker exec -it ai_native_redis redis-cli INFO stats | grep -E "total_commands_processed|keyspace_hits|keyspace_misses|used_memory_human"
```

### PowerShell Status Dashboard
```powershell
Write-Host "`n=== REDIS STATUS ===" -ForegroundColor Cyan
docker exec ai_native_redis redis-cli INFO stats | Select-String "total_commands_processed|keyspace_hits|keyspace_misses"
docker exec ai_native_redis redis-cli INFO memory | Select-String "used_memory_human|maxmemory"
Write-Host "`n=== API HEALTH ===" -ForegroundColor Cyan
curl http://localhost:8000/health -UseBasicParsing | ConvertFrom-Json | ConvertTo-Json
```

## 🔐 Security

### Set Password (Production)
```bash
# In docker-compose.production.yml, Redis starts with:
# command: redis-server --requirepass ${REDIS_PASSWORD}

# Then connect with:
docker exec -it ai_native_redis redis-cli -a YOUR_PASSWORD
```

### Disable Dangerous Commands (Production)
```bash
# Add to Redis config or command:
# --rename-command FLUSHALL ""
# --rename-command FLUSHDB ""
# --rename-command CONFIG ""
```

## 📚 Learn More

- [Redis Commands Reference](https://redis.io/commands)
- [Redis CLI Documentation](https://redis.io/topics/rediscli)
- [Project Redis Integration Guide](docs/REDIS_INTEGRATION.md)

---

**Quick Test Everything:**
```bash
# PowerShell One-Liner
docker-compose ps redis; curl http://localhost:8000/api/v3/system/redis/test -Method POST -UseBasicParsing | ConvertFrom-Json
```
