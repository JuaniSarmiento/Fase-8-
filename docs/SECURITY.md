# Security Guide - AI-Native Classroom

## 🔒 Comprehensive Security Implementation

This document describes all security measures implemented in the AI-Native Classroom platform.

---

## 1. Authentication & Authorization

### JWT Token Security
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Access Token Expiry**: 30 minutes (configurable)
- **Refresh Token Expiry**: 7 days (configurable)
- **Secret Key**: Minimum 32 characters (64 recommended)
- **Production Validation**: Prevents use of default/weak keys

### Password Security
- **Hashing**: bcrypt with 12 rounds
- **Strength Requirements**:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character
- **Max Length**: 128 characters (prevent DoS)

### Role-Based Access Control (RBAC)
- **Roles**: admin, teacher, student
- **Endpoint Protection**: Dependencies for role verification
- **Active User Check**: Ensures account is not suspended

---

## 2. Input Validation & Sanitization

### Implemented Validators
- **Username**: 3-30 alphanumeric characters, underscores, hyphens
- **Email**: RFC-compliant email format validation
- **Filename**: Path traversal prevention, dangerous character filtering
- **Integer**: Range validation with min/max bounds
- **JSON**: Size limits to prevent DoS (default 100KB)
- **SQL Identifiers**: Alphanumeric and underscore only

### XSS Protection
- **HTML Escaping**: All user inputs escaped before display
- **Pattern Detection**: Blocks `<script>`, `javascript:`, event handlers
- **Exempt Paths**: Code submission endpoints (students need to submit code)

### SQL Injection Protection
- **Parameterized Queries**: All database queries use SQLAlchemy ORM
- **Pattern Detection**: Middleware blocks suspicious SQL patterns
- **Identifier Sanitization**: Table/column names sanitized

### Path Traversal Prevention
- **Filename Validation**: Blocks `../`, `..\\` patterns
- **Allowed Directory Validation**: Ensures files within allowed paths

---

## 3. Rate Limiting & DDoS Protection

### Global Rate Limits
- **Per Minute**: 60 requests (configurable)
- **Per Hour**: 1000 requests (configurable)
- **Identifier**: Client IP address (supports X-Forwarded-For)
- **Response**: 429 Too Many Requests with Retry-After header

### Endpoint-Specific Limits
- **Authentication**: 5 attempts/minute, 20/hour (brute force protection)
- **File Upload**: 10 uploads/minute, 50/hour
- **Exempt Paths**: Health checks, metrics

### DDoS Mitigations
- **Sliding Window**: Accurate rate counting
- **Automatic Cleanup**: Old entries removed periodically
- **Per-Client Tracking**: Independent limits per IP

---

## 4. HTTP Security Headers

### Implemented Headers
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; ...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=(), ...
```

### Protection Against
- **Clickjacking**: X-Frame-Options DENY
- **MIME Sniffing**: X-Content-Type-Options nosniff
- **XSS**: CSP + X-XSS-Protection
- **MITM**: HSTS (forces HTTPS)
- **Information Leakage**: Referrer-Policy, removed Server header

---

## 5. CORS Configuration

### Production Settings
- **Allowed Origins**: Explicitly listed (no wildcards)
- **Allowed Methods**: GET, POST, PUT, DELETE, PATCH only
- **Credentials**: Enabled (allows cookies/auth headers)
- **Preflight Cache**: 1 hour (reduces overhead)
- **Exposed Headers**: Rate limit headers

### Configuration
```python
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

## 6. Code Execution Security

### Dangerous Pattern Detection
Blocks submissions containing:
- `__import__`, `exec()`, `eval()`, `compile()`
- File operations: `open()`, `file()`
- System access: `os.*`, `sys.*`, `subprocess.*`
- Network: `socket.*`, `urllib.*`, `requests.*`
- Introspection: `globals()`, `locals()`, `vars()`, `__builtins__`

### Safe Execution Environment
- **Sandboxed**: Code runs in isolated container
- **Resource Limits**: CPU, memory, time constraints
- **No Network**: Exercises cannot make external requests
- **Read-Only**: Limited filesystem access

---

## 7. Logging & Monitoring

### Request Logging
- **All Requests**: Method, path, client IP, status code
- **Sensitive Data**: Auth headers/cookies filtered from logs
- **Security Events**: Failed auth, rate limits, blocked requests

### Security Event Monitoring
- **Failed Login Attempts**: Track and alert on patterns
- **Rate Limit Violations**: Identify potential attacks
- **SQL Injection Attempts**: Log and block
- **XSS Attempts**: Log and block

### Log Levels
- **Production**: INFO level minimum
- **Development**: DEBUG level for troubleshooting

---

## 8. Database Security

### Connection Security
- **SSL/TLS**: Required in production (`DB_SSL_MODE=require`)
- **Credentials**: Strong passwords, never in code
- **Connection Pool**: Limited size (10 default, 20 max overflow)
- **Timeout**: 30 seconds (prevents hanging connections)

### Query Protection
- **ORM Only**: SQLAlchemy prevents raw SQL injection
- **Parameterized**: All queries use parameter binding
- **Transaction Management**: ACID compliance
- **Read Replicas**: Separate read/write for scaling (future)

---

## 9. Frontend Security

### Token Storage
- **localStorage**: Access tokens stored client-side
- **HttpOnly Cookies**: Preferred for production (future enhancement)
- **Automatic Expiry**: Tokens removed on logout

### XSS Prevention
- **React**: Automatic escaping of JSX content
- **No dangerouslySetInnerHTML**: Avoided throughout codebase
- **Content Security Policy**: Restricts inline scripts (with eval for Monaco)

### CSRF Protection
- **Same-Origin**: Cookies with SameSite attribute (future)
- **JWT in Headers**: Tokens in Authorization header (current)

---

## 10. Deployment Security

### Environment Variables
- **No Defaults in Production**: All secrets must be provided
- **Secret Key Validation**: Minimum length, no default values
- **Secure Generation**: Commands provided for strong keys

### Docker Security
- **Non-Root User**: Container runs as non-privileged user (future)
- **Resource Limits**: CPU and memory constraints
- **Read-Only Filesystem**: Where possible (future)
- **Minimal Image**: Alpine-based for smaller attack surface

### Network Security
- **Firewall**: Only necessary ports exposed
- **Internal Network**: Database not accessible from internet
- **TLS/SSL**: All external connections encrypted

---

## 11. Security Checklist for Production

### Pre-Deployment
- [ ] Generate unique SECRET_KEY (64+ characters)
- [ ] Generate unique JWT_SECRET_KEY (64+ characters)
- [ ] Set strong database password (16+ characters)
- [ ] Configure ALLOWED_ORIGINS with actual domain(s)
- [ ] Set ENVIRONMENT=production
- [ ] Set DEBUG=False
- [ ] Enable SSL for database (DB_SSL_MODE=require)
- [ ] Configure rate limits appropriately
- [ ] Set up error monitoring (Sentry)
- [ ] Configure logging to secure location

### Post-Deployment
- [ ] Verify HTTPS is enforced (HSTS header)
- [ ] Test CORS configuration
- [ ] Verify rate limiting is working
- [ ] Check security headers in responses
- [ ] Test authentication flow
- [ ] Verify role-based access control
- [ ] Monitor logs for security events
- [ ] Set up automated backups
- [ ] Configure database replication
- [ ] Test disaster recovery procedures

### Ongoing Maintenance
- [ ] Rotate secrets every 90 days
- [ ] Update dependencies regularly
- [ ] Review access logs weekly
- [ ] Monitor failed login attempts
- [ ] Check for CVEs in dependencies
- [ ] Perform security audits quarterly
- [ ] Update SSL certificates before expiry
- [ ] Review and update firewall rules
- [ ] Test backup restoration monthly

---

## 12. Security Incident Response

### Detection
- **Failed Auth Attempts**: Alert after 5 failed logins
- **Rate Limit Violations**: Alert after sustained violations
- **SQL Injection**: Immediate alert and IP block
- **Unusual Activity**: Spikes in errors, slow queries

### Response
1. **Identify**: Determine scope and impact
2. **Contain**: Block malicious IPs, disable compromised accounts
3. **Eradicate**: Remove malicious code, patch vulnerabilities
4. **Recover**: Restore from backups if needed
5. **Lessons Learned**: Update security measures

### Contact
- **Security Team**: security@yourdomain.com
- **On-Call**: +1-XXX-XXX-XXXX

---

## 13. Compliance & Standards

### Frameworks
- **OWASP Top 10**: Addressed all major vulnerabilities
- **CWE/SANS Top 25**: Mitigated common weaknesses
- **ISO 27001**: Information security management practices

### Data Protection
- **GDPR**: User data handling and privacy (if applicable)
- **COPPA**: Student data protection (if under 13)
- **FERPA**: Educational records protection (US)

---

## 14. Security Testing

### Automated Testing
- **SAST**: Static analysis (Bandit for Python)
- **Dependency Scanning**: Check for vulnerable packages
- **Unit Tests**: Security-focused test cases

### Manual Testing
- **Penetration Testing**: Annual third-party audit
- **Code Review**: Security-focused reviews
- **Threat Modeling**: Identify potential attack vectors

---

## 15. Security Tools & Commands

### Generate Secure Keys
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate JWT_SECRET_KEY  
python -c "import secrets; print(secrets.token_hex(32))"

# Generate secure password
python -c "import secrets, string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for _ in range(20)))"
```

### Check Dependencies
```bash
# Check for known vulnerabilities
pip install safety
safety check

# Update dependencies
pip list --outdated
pip install --upgrade package_name
```

### Database Backup
```bash
# Backup PostgreSQL
pg_dump -U postgres ai_native > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
psql -U postgres ai_native < backup_20240204_120000.sql
```

---

## 16. Support & Resources

### Documentation
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

### Tools
- [Mozilla Observatory](https://observatory.mozilla.org/)
- [Security Headers](https://securityheaders.com/)
- [SSL Labs](https://www.ssllabs.com/ssltest/)

---

**Last Updated**: February 4, 2026
**Version**: 1.0
**Author**: Security Team
