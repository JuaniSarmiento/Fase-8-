"""Rate Limiting Middleware for API Protection.

Protects against:
- Brute force attacks
- DDoS attempts
- API abuse
"""
from __future__ import annotations

import time
from typing import Dict, Tuple, Optional
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory rate limiter with sliding window."""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        # Storage: {identifier: [(timestamp, count)]}
        self.minute_window: Dict[str, list] = defaultdict(list)
        self.hour_window: Dict[str, list] = defaultdict(list)
        
    def _clean_old_entries(self, window: Dict[str, list], max_age: float):
        """Remove entries older than max_age seconds."""
        current_time = time.time()
        for identifier in list(window.keys()):
            window[identifier] = [
                (ts, count) for ts, count in window[identifier]
                if current_time - ts < max_age
            ]
            if not window[identifier]:
                del window[identifier]
    
    def is_allowed(self, identifier: str) -> Tuple[bool, Optional[str]]:
        """Check if request is allowed. Returns (allowed, error_message)."""
        current_time = time.time()
        
        # Clean old entries
        self._clean_old_entries(self.minute_window, 60)
        self._clean_old_entries(self.hour_window, 3600)
        
        # Check minute limit
        minute_requests = sum(count for _, count in self.minute_window[identifier])
        if minute_requests >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        # Check hour limit
        hour_requests = sum(count for _, count in self.hour_window[identifier])
        if hour_requests >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
        
        # Add current request
        self.minute_window[identifier].append((current_time, 1))
        self.hour_window[identifier].append((current_time, 1))
        
        return True, None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting per IP address."""
    
    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute, requests_per_hour)
        self.exempt_paths = {"/health", "/metrics", "/api/v3/system/health"}
        
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier (IP address or user ID)."""
        # Try to get real IP from headers (for reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Get client identifier
        identifier = self._get_client_identifier(request)
        
        # Check rate limit
        allowed, error_message = self.limiter.is_allowed(identifier)
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {identifier} on {request.method} {request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_message,
                headers={"Retry-After": "60"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.limiter.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.limiter.requests_per_hour)
        
        return response


# Specific rate limiters for sensitive endpoints
class AuthRateLimiter(RateLimiter):
    """Stricter rate limiter for authentication endpoints."""
    
    def __init__(self):
        # 5 attempts per minute, 20 per hour (prevent brute force)
        super().__init__(requests_per_minute=5, requests_per_hour=20)


class UploadRateLimiter(RateLimiter):
    """Rate limiter for file upload endpoints."""
    
    def __init__(self):
        # 10 uploads per minute, 50 per hour
        super().__init__(requests_per_minute=10, requests_per_hour=50)
