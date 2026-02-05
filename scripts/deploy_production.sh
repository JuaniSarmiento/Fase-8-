#!/bin/bash

# ============================================================================
# Production Deployment Script with Security Checks
# ============================================================================
# This script validates security requirements before deploying to production
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==================== Functions ====================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_required_var() {
    local var_name=$1
    if [ -z "${!var_name:-}" ]; then
        log_error "Required environment variable $var_name is not set"
        return 1
    fi
    log_info "$var_name is set"
    return 0
}

check_secret_strength() {
    local var_name=$1
    local min_length=32
    local value="${!var_name:-}"
    
    if [ -z "$value" ]; then
        log_error "$var_name is not set"
        return 1
    fi
    
    if [ ${#value} -lt $min_length ]; then
        log_error "$var_name is too short (${#value} chars, minimum $min_length)"
        return 1
    fi
    
    # Check for default/weak values
    local weak_secrets=(
        "fase8-dev-secret-key-change-in-production-please"
        "fase8-jwt-secret-key-development-only"
        "secret"
        "changeme"
        "password"
        "12345"
    )
    
    for weak in "${weak_secrets[@]}"; do
        if [ "$value" = "$weak" ]; then
            log_error "$var_name contains a default/weak value"
            return 1
        fi
    done
    
    log_info "$var_name has sufficient strength (${#value} chars)"
    return 0
}

# ==================== Pre-Deployment Checks ====================

log_info "Starting pre-deployment security checks..."
echo

# Check if .env file exists
if [ ! -f .env ]; then
    log_error ".env file not found"
    log_info "Copy .env.production.example to .env and fill in values"
    exit 1
fi

# Source environment variables
source .env

# Initialize error counter
ERRORS=0

# Check environment
log_info "Checking ENVIRONMENT setting..."
if [ "${ENVIRONMENT:-}" != "production" ]; then
    log_error "ENVIRONMENT must be set to 'production'"
    ERRORS=$((ERRORS + 1))
fi

# Check DEBUG setting
log_info "Checking DEBUG setting..."
if [ "${DEBUG:-}" != "False" ] && [ "${DEBUG:-}" != "false" ]; then
    log_error "DEBUG must be set to False in production"
    ERRORS=$((ERRORS + 1))
fi

# Check required variables
log_info "Checking required environment variables..."
REQUIRED_VARS=(
    "DATABASE_URL"
    "SECRET_KEY"
    "JWT_SECRET_KEY"
    "ALLOWED_ORIGINS"
    "ALLOWED_HOSTS"
)

for var in "${REQUIRED_VARS[@]}"; do
    if ! check_required_var "$var"; then
        ERRORS=$((ERRORS + 1))
    fi
done

# Check secret strength
log_info "Checking secret strength..."
SECRET_VARS=(
    "SECRET_KEY"
    "JWT_SECRET_KEY"
)

for var in "${SECRET_VARS[@]}"; do
    if ! check_secret_strength "$var"; then
        ERRORS=$((ERRORS + 1))
    fi
done

# Check database password
log_info "Checking database configuration..."
if [[ "$DATABASE_URL" == *"postgres:postgres@"* ]]; then
    log_error "Using default database password 'postgres'"
    ERRORS=$((ERRORS + 1))
fi

# Check CORS configuration
log_info "Checking CORS configuration..."
if [[ "$ALLOWED_ORIGINS" == *"*"* ]]; then
    log_error "ALLOWED_ORIGINS contains wildcard (*) - this is insecure"
    ERRORS=$((ERRORS + 1))
fi

if [[ "$ALLOWED_ORIGINS" == *"localhost"* ]]; then
    log_warning "ALLOWED_ORIGINS contains localhost - remove for production"
fi

# Check JWT expiration
log_info "Checking JWT expiration settings..."
JWT_EXPIRE=${JWT_ACCESS_TOKEN_EXPIRE_MINUTES:-30}
if [ "$JWT_EXPIRE" -gt 1440 ]; then
    log_warning "JWT_ACCESS_TOKEN_EXPIRE_MINUTES is set to $JWT_EXPIRE minutes (> 24 hours)"
    log_warning "Consider using shorter expiration for better security"
fi

# Check for development dependencies
log_info "Checking for development dependencies..."
if grep -q "pytest" requirements.txt 2>/dev/null; then
    log_warning "Development dependencies found in requirements.txt"
    log_warning "Consider using separate requirements files for production"
fi

# Check Docker
log_info "Checking Docker..."
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    ERRORS=$((ERRORS + 1))
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    log_error "Docker Compose is not installed"
    ERRORS=$((ERRORS + 1))
fi

# Check SSL certificates (if using nginx)
if [ -d "nginx/ssl" ]; then
    log_info "Checking SSL certificates..."
    if [ ! -f "nginx/ssl/server.crt" ] || [ ! -f "nginx/ssl/server.key" ]; then
        log_warning "SSL certificates not found in nginx/ssl/"
        log_warning "Generate certificates or configure Let's Encrypt"
    else
        log_info "SSL certificates found"
    fi
fi

# ==================== Results ====================

echo
echo "========================================"
if [ $ERRORS -eq 0 ]; then
    log_info "All security checks passed! ✓"
    echo "========================================"
    echo
    
    # Ask for confirmation
    read -p "Do you want to proceed with deployment? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log_info "Deployment cancelled"
        exit 0
    fi
    
    # Start deployment
    log_info "Starting deployment..."
    echo
    
    # Build images
    log_info "Building Docker images..."
    docker-compose -f docker-compose.production.yml build --no-cache
    
    # Start services
    log_info "Starting services..."
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    log_info "Checking service health..."
    docker-compose -f docker-compose.production.yml ps
    
    # Test backend health endpoint
    log_info "Testing backend health endpoint..."
    BACKEND_PORT=${BACKEND_PORT:-8000}
    if curl -f "http://localhost:${BACKEND_PORT}/health" > /dev/null 2>&1; then
        log_info "Backend is healthy ✓"
    else
        log_error "Backend health check failed"
        exit 1
    fi
    
    echo
    log_info "Deployment completed successfully! ✓"
    log_info "Backend: http://localhost:${BACKEND_PORT}"
    log_info "Prometheus: http://localhost:${PROMETHEUS_PORT:-9090}"
    log_info "Grafana: http://localhost:${GRAFANA_PORT:-3000}"
    
else
    log_error "Security checks failed with $ERRORS error(s)"
    echo "========================================"
    echo
    log_error "Please fix the issues above before deploying to production"
    exit 1
fi
