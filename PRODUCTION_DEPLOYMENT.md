"""Production Deployment Guide - AI-Native Learning Platform

This guide covers deploying the application to production with best practices.
"""

# AI-Native Learning Platform - Production Deployment Guide

## 📋 Pre-Deployment Checklist

### 1. Environment Configuration

#### Backend Environment Variables (.env)
```bash
# Copy the example file
cp .env.production.example .env

# CRITICAL: Update these values
- JWT_SECRET_KEY: Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- DB_PASSWORD: Strong database password (min 16 characters)
- REDIS_PASSWORD: Strong Redis password
- CHROMA_AUTH_CREDENTIALS: Generate random token
- OPENAI_API_KEY: Your OpenAI API key
```

#### Frontend Environment Variables (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v3
NEXT_PUBLIC_ENVIRONMENT=production
```

### 2. Security Hardening

#### ✅ Completed
- [x] Rate limiting enabled (5 req/min for auth, 100 req/min for API)
- [x] Security headers (CSP, HSTS, X-Frame-Options, etc.)
- [x] Input validation and sanitization
- [x] Password strength requirements (8+ chars, uppercase, lowercase, digit)
- [x] SQL injection prevention (parameterized queries)
- [x] XSS prevention (HTML escaping)
- [x] CORS properly configured
- [x] Error handling without information leakage

#### 🔒 Additional Steps
- [ ] Enable HTTPS/TLS certificates (Let's Encrypt recommended)
- [ ] Configure firewall rules (only allow ports 80, 443)
- [ ] Set up SSH key authentication (disable password auth)
- [ ] Configure fail2ban for brute force protection
- [ ] Enable database SSL connections
- [ ] Set up VPN for database access

### 3. Database Configuration

#### PostgreSQL Optimization
```sql
-- Create database with optimal settings
CREATE DATABASE ai_native
  WITH ENCODING='UTF8'
  LC_COLLATE='en_US.UTF-8'
  LC_CTYPE='en_US.UTF-8'
  TEMPLATE=template0;

-- Enable required extensions
\c ai_native
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create indexes for performance
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_users_username ON users(username);
CREATE INDEX CONCURRENTLY idx_sessions_student_id ON sessions_v2(student_id);
CREATE INDEX CONCURRENTLY idx_sessions_activity_id ON sessions_v2(activity_id);
```

#### Backup Strategy
```bash
# Daily automated backups
0 2 * * * /usr/local/bin/backup-database.sh

# Backup script
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h postgres -U postgres ai_native | gzip > $BACKUP_DIR/ai_native_$DATE.sql.gz
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### 4. Docker Production Configuration

#### Build Production Images
```bash
# Backend
docker build -f Dockerfile.production -t ai-native-backend:latest .

# Frontend
cd frontend
docker build -f Dockerfile.production -t ai-native-frontend:latest .
```

#### Deploy with Docker Compose
```bash
# Use production compose file
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Check health
docker-compose -f docker-compose.production.yml ps
```

### 5. Monitoring and Logging

#### Log Management
```bash
# Logs are stored in:
/app/logs/application.log  # All logs
/app/logs/errors.log       # Errors only
/app/logs/security.log     # Auth/security events

# Rotate logs with logrotate
cat > /etc/logrotate.d/ai-native << EOF
/app/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
EOF
```

#### Health Checks
```bash
# System health
curl https://api.yourdomain.com/health

# Detailed health with auth
curl -H "Authorization: Bearer TOKEN" https://api.yourdomain.com/api/v3/system/health/detailed

# Redis stats
curl -H "Authorization: Bearer TOKEN" https://api.yourdomain.com/api/v3/system/redis/stats
```

#### Monitoring Tools (Recommended)
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- **Sentry**: Error tracking
- **UptimeRobot**: Uptime monitoring

### 6. Performance Optimization

#### Redis Configuration
```conf
# redis.conf production settings
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### Database Connection Pooling
Already configured in code:
- Pool size: 20 connections
- Max overflow: 10
- Pool recycle: 3600 seconds

#### CDN for Static Assets
- Use CloudFlare or AWS CloudFront
- Cache static assets (CSS, JS, images)
- Enable Brotli/Gzip compression

### 7. SSL/TLS Setup

#### Let's Encrypt with Certbot
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo crontab -e
0 3 * * * /usr/bin/certbot renew --quiet
```

#### Nginx Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Strong SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🚀 Deployment Steps

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/yourrepo/ai-native-platform.git
cd ai-native-platform

# 2. Configure environment
cp .env.production.example .env
nano .env  # Update all values

# 3. Build and start services
docker-compose -f docker-compose.production.yml up -d

# 4. Run database migrations
docker-compose exec backend alembic upgrade head

# 5. Verify deployment
curl https://api.yourdomain.com/health
```

### Option 2: Kubernetes

```bash
# Create namespace
kubectl create namespace ai-native

# Create secrets
kubectl create secret generic ai-native-secrets \
  --from-env-file=.env \
  --namespace=ai-native

# Deploy
kubectl apply -f k8s/ --namespace=ai-native

# Check status
kubectl get pods --namespace=ai-native
```

## 📊 Post-Deployment Monitoring

### Key Metrics to Monitor

1. **Application Health**
   - Uptime percentage (target: 99.9%)
   - Response times (target: <200ms p95)
   - Error rates (target: <0.1%)

2. **Database Performance**
   - Query execution times
   - Connection pool usage
   - Active connections
   - Cache hit rates

3. **Redis Performance**
   - Memory usage
   - Cache hit rate (target: >80%)
   - Commands per second

4. **System Resources**
   - CPU usage (target: <70%)
   - Memory usage (target: <80%)
   - Disk I/O
   - Network bandwidth

### Alerting Rules

Set up alerts for:
- API response time > 1s
- Error rate > 1%
- Database connections > 80%
- Memory usage > 90%
- Disk space < 10%
- SSL certificate expiring < 30 days

## 🔄 Maintenance

### Regular Tasks

**Daily**
- Check application logs for errors
- Verify backup completion
- Monitor resource usage

**Weekly**
- Review security logs
- Update dependencies if needed
- Check disk space

**Monthly**
- Security audit
- Performance review
- Database optimization (VACUUM, ANALYZE)
- Review and rotate logs

### Database Maintenance

```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check slow queries
SELECT query, calls, mean_exec_time, max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

## 🆘 Troubleshooting

### Common Issues

**Backend not starting**
```bash
# Check logs
docker-compose logs backend

# Check database connection
docker-compose exec backend python -c "from sqlalchemy import create_engine; engine = create_engine('DATABASE_URL'); print('OK')"
```

**High memory usage**
```bash
# Check Redis memory
docker-compose exec redis redis-cli INFO memory

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

**Slow queries**
```bash
# Enable query logging
docker-compose exec postgres psql -U postgres -d ai_native -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"
docker-compose exec postgres psql -U postgres -c "SELECT pg_reload_conf();"
```

## 📞 Support

- Documentation: `/docs`
- Issues: GitHub Issues
- Email: support@yourdomain.com

---

**Last Updated**: February 2026
**Version**: 3.0.0
