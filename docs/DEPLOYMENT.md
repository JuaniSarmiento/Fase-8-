# 🚀 Production Deployment Guide

## Security-First Deployment for AI-Native Classroom

This guide walks you through deploying the AI-Native Classroom platform to production with all security measures in place.

---

## 📋 Pre-Deployment Checklist

### 1. Environment Preparation

- [ ] **Server Requirements Met**
  - Ubuntu 20.04 LTS or newer (recommended)
  - 4 CPU cores minimum (8 recommended)
  - 8GB RAM minimum (16GB recommended)
  - 50GB disk space minimum (100GB recommended)
  - Docker 20.10+ and Docker Compose installed

- [ ] **Domain & SSL**
  - Domain name registered and DNS configured
  - SSL certificate obtained (Let's Encrypt or commercial)
  - Subdomain for API (api.yourdomain.com)
  - Subdomain for app (app.yourdomain.com)

- [ ] **External Services**
  - LLM API keys obtained (Mistral, OpenAI, or Anthropic)
  - Database backup solution configured
  - Monitoring service ready (optional: Sentry, Datadog)
  - Email service configured (optional: SendGrid, AWS SES)

---

## 🔐 Step 1: Generate Secure Secrets

### Generate SECRET_KEY and JWT_SECRET_KEY

```bash
# Generate SECRET_KEY (64 characters)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate JWT_SECRET_KEY (64 characters, DIFFERENT from SECRET_KEY)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate database password (20 characters)
python3 -c "import secrets, string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for _ in range(20)))"
```

**CRITICAL**: Save these in a secure password manager. Never commit to git.

---

## ⚙️ Step 2: Configure Environment Variables

### Create Production Environment File

```bash
# Copy the production example
cp .env.production.example .env

# Edit with your values
nano .env
```

### Required Variables

```bash
# CRITICAL: Set these correctly!
ENVIRONMENT=production
DEBUG=False

# Secrets (use generated values from Step 1)
SECRET_KEY=your_64_char_secret_key_here
JWT_SECRET_KEY=your_different_64_char_jwt_key_here

# Database (use strong password)
DATABASE_URL=postgresql+asyncpg://postgres:your_db_password@postgres:5432/ai_native

# CORS (your actual domains)
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,app.yourdomain.com

# LLM Provider (choose one)
MISTRAL_API_KEY=your_mistral_api_key
# OR
OPENAI_API_KEY=your_openai_api_key
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key
```

---

## 🐳 Step 3: Prepare Docker

### SSL Certificates

```bash
# Create SSL directory
mkdir -p nginx/ssl

# Option 1: Let's Encrypt (recommended)
sudo certbot certonly --standalone -d yourdomain.com -d app.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/server.crt
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/server.key
sudo chmod 644 nginx/ssl/server.crt
sudo chmod 600 nginx/ssl/server.key

# Option 2: Self-signed (development only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/server.key -out nginx/ssl/server.crt
```

### Nginx Configuration

```bash
# Create nginx config
mkdir -p nginx
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name yourdomain.com app.yourdomain.com;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com app.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/server.crt;
        ssl_certificate_key /etc/nginx/ssl/server.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        location /api {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            proxy_pass http://frontend:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF
```

---

## 🚢 Step 4: Deploy with Security Validation

### Run Security Checks

```bash
# Make script executable
chmod +x scripts/deploy_production.sh

# Run deployment script (includes security checks)
./scripts/deploy_production.sh
```

The script will:
1. ✅ Validate all required environment variables
2. ✅ Check secret key strength
3. ✅ Verify production configuration
4. ✅ Ensure no default passwords
5. ✅ Validate CORS settings
6. ✅ Build Docker images
7. ✅ Start services
8. ✅ Run health checks

### Manual Deployment (Alternative)

```bash
# Build images
docker-compose -f docker-compose.production.yml build --no-cache

# Start services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f backend
```

---

## 🔍 Step 5: Verify Deployment

### Health Checks

```bash
# Backend health
curl https://api.yourdomain.com/health

# Expected response:
# {"status":"healthy","version":"3.0.0","checks":{"database":"ok"}}

# Test authentication
curl -X POST https://api.yourdomain.com/api/v3/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}'
```

### Security Headers Check

```bash
# Check security headers
curl -I https://api.yourdomain.com/api/v3/system/info

# Should include:
# Strict-Transport-Security: max-age=31536000
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# Content-Security-Policy: ...
```

### SSL/TLS Check

```bash
# Test SSL configuration
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Or use online tool:
# https://www.ssllabs.com/ssltest/
```

---

## 📊 Step 6: Setup Monitoring

### Prometheus Metrics

Access Prometheus at `http://your-server:9090`

Key metrics to monitor:
- `http_requests_total` - Total requests
- `http_request_duration_seconds` - Request latency
- `python_gc_objects_collected_total` - Memory usage
- `process_cpu_seconds_total` - CPU usage

### Grafana Dashboards

1. Access Grafana at `http://your-server:3000`
2. Login with credentials from `.env`
3. Add Prometheus as data source
4. Import dashboards:
   - FastAPI Dashboard (ID: 14961)
   - PostgreSQL Dashboard (ID: 9628)

### Log Monitoring

```bash
# View application logs
docker-compose -f docker-compose.production.yml logs -f backend

# View all logs
docker-compose -f docker-compose.production.yml logs -f

# Export logs to file
docker-compose -f docker-compose.production.yml logs > deployment.log
```

---

## 🔄 Step 7: Database Backup

### Automated Backups

```bash
# Create backup script
cat > scripts/backup_database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ai_native_$TIMESTAMP.sql"

docker exec ai_native_postgres_prod pg_dump -U postgres ai_native > "$BACKUP_FILE"
gzip "$BACKUP_FILE"

# Keep only last 30 days
find $BACKUP_DIR -name "ai_native_*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
EOF

chmod +x scripts/backup_database.sh

# Add to cron (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/scripts/backup_database.sh") | crontab -
```

### Manual Backup

```bash
# Backup
docker exec ai_native_postgres_prod pg_dump -U postgres ai_native > backup.sql

# Restore
docker exec -i ai_native_postgres_prod psql -U postgres ai_native < backup.sql
```

---

## 🛡️ Step 8: Security Hardening

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Optionally, allow monitoring ports (only from specific IPs)
sudo ufw allow from YOUR_IP to any port 9090  # Prometheus
sudo ufw allow from YOUR_IP to any port 3000  # Grafana
```

### Fail2Ban Setup

```bash
# Install fail2ban
sudo apt-get install fail2ban

# Configure for nginx
sudo cat > /etc/fail2ban/jail.local << 'EOF'
[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=ReqLimit, port="http,https", protocol=tcp]
logpath = /var/log/nginx/error.log
findtime = 600
bantime = 3600
maxretry = 10
EOF

sudo systemctl restart fail2ban
```

### Auto-Updates

```bash
# Enable unattended upgrades (Ubuntu)
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📱 Step 9: Frontend Deployment

### Build Frontend

```bash
cd frontend

# Install dependencies
npm install --production

# Build
npm run build

# Start production server
npm start
```

### Deploy with Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com
# NEXT_PUBLIC_ENVIRONMENT=production
```

### Deploy with Docker

Already included in `docker-compose.production.yml` if needed.

---

## 🔐 Step 10: Post-Deployment Security

### 1. Change Default Passwords

```bash
# Grafana admin password
docker exec -it ai_native_grafana grafana-cli admin reset-admin-password NEW_PASSWORD

# Create non-admin users for team access
```

### 2. Setup SSL Auto-Renewal

```bash
# Certbot auto-renewal (if using Let's Encrypt)
sudo certbot renew --dry-run

# Add to cron
(crontab -l 2>/dev/null; echo "0 0 * * * certbot renew --quiet") | crontab -
```

### 3. Security Scan

```bash
# Scan for vulnerabilities
docker scan ai_native_backend_prod

# Check dependencies
cd backend
pip install safety
safety check
```

### 4. Performance Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Load test (adjust concurrent connections)
ab -n 1000 -c 10 https://api.yourdomain.com/health
```

---

## 📞 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs backend

# Check environment variables
docker-compose -f docker-compose.production.yml config

# Restart service
docker-compose -f docker-compose.production.yml restart backend
```

### Database Connection Issues

```bash
# Test database connection
docker exec -it ai_native_postgres_prod psql -U postgres -d ai_native

# Check database logs
docker logs ai_native_postgres_prod
```

### High CPU/Memory Usage

```bash
# Check resource usage
docker stats

# Increase resource limits in docker-compose.production.yml
```

---

## 🔄 Updates & Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose -f docker-compose.production.yml build --no-cache

# Update services (zero-downtime)
docker-compose -f docker-compose.production.yml up -d --no-deps backend

# Run migrations if needed
docker exec ai_native_backend_prod python -m alembic upgrade head
```

### Database Migrations

```bash
# Create migration
docker exec ai_native_backend_prod alembic revision --autogenerate -m "description"

# Apply migration
docker exec ai_native_backend_prod alembic upgrade head

# Rollback
docker exec ai_native_backend_prod alembic downgrade -1
```

---

## 📚 Additional Resources

- [Security Guide](./SECURITY.md)
- [Frontend Security](./FRONTEND_SECURITY.py)
- [API Documentation](https://api.yourdomain.com/docs)
- [Monitoring Dashboard](http://your-server:3000)

---

## ⚠️ Important Reminders

1. **Never commit .env files** to version control
2. **Rotate secrets every 90 days**
3. **Keep backups** in multiple locations
4. **Monitor logs** regularly for suspicious activity
5. **Update dependencies** monthly
6. **Test disaster recovery** procedures quarterly
7. **Review access logs** weekly
8. **Keep documentation** up to date

---

## 🆘 Support

For issues or questions:
- Security: security@yourdomain.com
- Technical: support@yourdomain.com
- Emergency: +1-XXX-XXX-XXXX

---

**Deployment Version**: 1.0  
**Last Updated**: February 4, 2026  
**Status**: Production Ready ✅
