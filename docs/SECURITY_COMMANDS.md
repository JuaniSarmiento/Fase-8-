# Security Commands Cheat Sheet

Quick reference for security-related commands and tools.

## 🔑 Generate Secrets

### SECRET_KEY (64 characters)
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### JWT_SECRET_KEY (64 characters, different from SECRET_KEY)
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Database Password (20 characters)
```bash
python -c "import secrets, string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for _ in range(20)))"
```

### Random String (custom length)
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🔍 Security Audits

### Run Security Audit Script
```bash
python scripts/security_audit.py
```

### Check Python Dependencies
```bash
pip install safety
safety check
```

### Scan for Secrets in Code
```bash
# Install truffleHog
pip install truffleHog

# Scan repository
trufflehog filesystem . --json
```

### Scan Docker Images
```bash
docker scan ai_native_backend_prod
```

---

## 🧪 Penetration Testing

### Test Rate Limiting
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 http://localhost:8000/api/v3/system/info

# Should see 429 responses after limit
```

### Test SQL Injection
```bash
# This should be blocked
curl "http://localhost:8000/api/v3/activities?id=1' OR '1'='1"

# Expected: 400 Bad Request
```

### Test XSS
```bash
# This should be sanitized
curl -X POST http://localhost:8000/api/v3/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"<script>alert(1)</script>","email":"test@test.com","password":"Test123!"}'

# Expected: 400 Bad Request or sanitized input
```

### Test CORS
```bash
# Test from unauthorized origin
curl -H "Origin: http://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS http://localhost:8000/api/v3/auth/login

# Should not return Access-Control-Allow-Origin: http://evil.com
```

---

## 🔒 SSL/TLS

### Generate Self-Signed Certificate (Development)
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout server.key -out server.crt
```

### Test SSL Configuration
```bash
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### Check Certificate Expiry
```bash
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

### Online SSL Test
```bash
# Use SSL Labs (paste URL in browser)
https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

---

## 📊 Security Headers

### Check Security Headers
```bash
curl -I http://localhost:8000/api/v3/system/info
```

### Online Header Check
```bash
# Use securityheaders.com (paste URL in browser)
https://securityheaders.com/?q=https://yourdomain.com
```

### Expected Headers
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; ...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

---

## 🗄️ Database Security

### Backup Database
```bash
# PostgreSQL backup
docker exec ai_native_postgres_prod pg_dump -U postgres ai_native > backup.sql

# Compressed backup
docker exec ai_native_postgres_prod pg_dump -U postgres ai_native | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore Database
```bash
# From plain SQL
docker exec -i ai_native_postgres_prod psql -U postgres ai_native < backup.sql

# From compressed
gunzip < backup_20240204.sql.gz | docker exec -i ai_native_postgres_prod psql -U postgres ai_native
```

### Check Database Connections
```bash
docker exec ai_native_postgres_prod psql -U postgres -d ai_native -c "
SELECT pid, usename, application_name, client_addr, state 
FROM pg_stat_activity 
WHERE datname = 'ai_native';
"
```

### Revoke Unnecessary Permissions
```sql
-- Example: Revoke public access
REVOKE ALL ON DATABASE ai_native FROM PUBLIC;

-- Grant specific permissions
GRANT CONNECT ON DATABASE ai_native TO app_user;
```

---

## 📝 Logging & Monitoring

### View Backend Logs
```bash
# Real-time logs
docker logs -f ai_native_backend_prod

# Last 100 lines
docker logs --tail 100 ai_native_backend_prod

# Logs with timestamps
docker logs -t ai_native_backend_prod
```

### Search Logs for Security Events
```bash
# Failed login attempts
docker logs ai_native_backend_prod | grep "401 UNAUTHORIZED"

# Rate limit violations
docker logs ai_native_backend_prod | grep "429"

# SQL injection attempts
docker logs ai_native_backend_prod | grep "SQL injection"
```

### Prometheus Metrics
```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# Filter specific metric
curl http://localhost:8000/metrics | grep http_requests_total
```

### Grafana Access
```bash
# Open in browser
open http://localhost:3000

# Default credentials (change these!)
# Username: admin
# Password: from .env GRAFANA_ADMIN_PASSWORD
```

---

## 🔥 Firewall Configuration

### UFW (Ubuntu)
```bash
# Enable firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow from specific IP only
sudo ufw allow from YOUR_IP to any port 9090  # Prometheus
sudo ufw allow from YOUR_IP to any port 3000  # Grafana

# Check status
sudo ufw status verbose

# Delete rule
sudo ufw delete allow 8000/tcp
```

### Fail2Ban
```bash
# Install
sudo apt-get install fail2ban

# Check status
sudo fail2ban-client status

# Check specific jail
sudo fail2ban-client status nginx-limit-req

# Unban IP
sudo fail2ban-client set nginx-limit-req unbanip YOUR_IP
```

---

## 🐳 Docker Security

### Scan Images for Vulnerabilities
```bash
# Scan specific image
docker scan ai_native_backend_prod

# Scan with specific severity
docker scan --severity high ai_native_backend_prod
```

### Check Running Containers
```bash
# List containers
docker ps

# Check container resources
docker stats

# Inspect container security
docker inspect ai_native_backend_prod | grep -A 10 SecurityOpt
```

### Update Images
```bash
# Pull latest base images
docker pull python:3.11-slim
docker pull postgres:15-alpine

# Rebuild with no cache
docker-compose -f docker-compose.production.yml build --no-cache

# Prune old images
docker image prune -a
```

---

## 🔄 Secrets Rotation

### Rotate SECRET_KEY
```bash
# 1. Generate new key
NEW_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# 2. Update .env
echo "SECRET_KEY=$NEW_KEY" >> .env

# 3. Restart services
docker-compose -f docker-compose.production.yml restart backend

# 4. Verify
curl http://localhost:8000/health
```

### Rotate Database Password
```bash
# 1. Generate new password
NEW_PASS=$(python -c "import secrets, string; chars = string.ascii_letters + string.digits; print(''.join(secrets.choice(chars) for _ in range(20)))")

# 2. Update PostgreSQL
docker exec ai_native_postgres_prod psql -U postgres -c "ALTER USER postgres PASSWORD '$NEW_PASS';"

# 3. Update .env
# 4. Restart backend
```

### Rotate JWT_SECRET_KEY
```bash
# WARNING: This will invalidate all existing tokens!

# 1. Notify users of logout
# 2. Generate new key
NEW_JWT=$(python -c "import secrets; print(secrets.token_hex(32))")

# 3. Update .env with new key
# 4. Restart backend
# 5. Users must login again
```

---

## 🧰 Useful Security Tools

### Install Security Tools
```bash
# Python security tools
pip install safety bandit

# Node.js security tools
npm install -g snyk

# General security
sudo apt-get install nmap nikto
```

### Run Bandit (Python Security Linter)
```bash
bandit -r backend/ -f json -o security_report.json
```

### Run Snyk (Dependency Scanner)
```bash
snyk test
snyk monitor
```

### Port Scanning
```bash
# Scan your server
nmap -sV localhost

# Check specific ports
nmap -p 80,443,8000 localhost
```

---

## 📞 Emergency Response

### Detect Active Attacks
```bash
# Check unusual connections
docker exec ai_native_backend_prod netstat -an | grep ESTABLISHED

# Check failed login attempts
docker logs ai_native_backend_prod | grep "401" | wc -l

# Check rate limit triggers
docker logs ai_native_backend_prod | grep "429" | tail -20
```

### Block Malicious IP
```bash
# Temporary block with UFW
sudo ufw deny from MALICIOUS_IP

# Permanent block
sudo ufw insert 1 deny from MALICIOUS_IP
```

### Emergency Shutdown
```bash
# Stop all services
docker-compose -f docker-compose.production.yml down

# Stop specific service
docker stop ai_native_backend_prod
```

### Restore from Backup
```bash
# 1. Stop services
docker-compose down

# 2. Restore database
gunzip < backup_latest.sql.gz | docker exec -i ai_native_postgres_prod psql -U postgres ai_native

# 3. Restart services
docker-compose up -d

# 4. Verify
curl http://localhost:8000/health
```

---

## ✅ Post-Deployment Checklist

```bash
# 1. Check all services are running
docker-compose ps

# 2. Verify health endpoints
curl http://localhost:8000/health

# 3. Check security headers
curl -I http://localhost:8000/api/v3/system/info

# 4. Test authentication
curl -X POST http://localhost:8000/api/v3/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!"}'

# 5. Verify rate limiting
ab -n 100 -c 20 http://localhost:8000/api/v3/system/info

# 6. Check logs for errors
docker logs --tail 50 ai_native_backend_prod

# 7. Verify database connection
docker exec ai_native_postgres_prod pg_isready

# 8. Check SSL certificate (production)
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | grep -A 2 "Verify return code"
```

---

**Last Updated**: February 4, 2026  
**Version**: 1.0  
**Maintained by**: Security Team
