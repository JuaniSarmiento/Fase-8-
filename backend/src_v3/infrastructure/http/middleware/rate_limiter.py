"""Rate Limiting Middleware for Production.

Prevents abuse and DDoS attacks by limiting requests per IP.
"""
from __future__ import annotations

import time
from typing import Dict, Tuple
from collections import defaultdict
from threading import Lock
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """Simple in-memory rate limiter using sliding window."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(
        self, 
        identifier: str, 
        max_requests: int, 
        window_seconds: int
    ) -> Tuple[bool, int]:
        """Check if request is allowed.
        
        Args:
            identifier: Unique identifier (e.g., IP address)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            (is_allowed, remaining_requests)
        """
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        with self.lock:
            # Remove old requests
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff_time
            ]
            
            request_count = len(self.requests[identifier])
            
            if request_count >= max_requests:
                return False, 0
            
            # Add current request
            self.requests[identifier].append(current_time)
            remaining = max_requests - request_count - 1
            
            return True, remaining
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """Clean up old entries to prevent memory bloat."""
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds
        
        with self.lock:
            keys_to_delete = []
            for identifier, timestamps in self.requests.items():
                # Remove old timestamps
                self.requests[identifier] = [
                    t for t in timestamps if t > cutoff_time
                ]
                # Mark for deletion if empty
                if not self.requests[identifier]:
                    keys_to_delete.append(identifier)
            
            for key in keys_to_delete:
                del self.requests[key]


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI.
    
    Different limits for different endpoint types:
    - Authentication endpoints: Stricter limits
    - API endpoints: Normal limits
    - Health checks: Unlimited
    """
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        
        # Rate limits: (max_requests, window_seconds)
        self.limits = {
            "auth": (5, 60),      # 5 requests per minute for auth
            "api": (100, 60),     # 100 requests per minute for API
            "default": (50, 60),  # 50 requests per minute default
        }
    
    def get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for client (IP address)."""
        # Try to get real IP from proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def get_rate_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit for given path."""
        if "/auth/" in path:
            return self.limits["auth"]
        elif "/api/" in path:
            return self.limits["api"]
        else:
            return self.limits["default"]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        if not self.enabled:
            return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/detailed"]:
            return await call_next(request)
        
        client_id = self.get_client_identifier(request)
        path = request.url.path
        max_requests, window = self.get_rate_limit(path)
        
        # Create unique key for endpoint and client
        identifier = f"{client_id}:{path}"
        
        is_allowed, remaining = rate_limiter.is_allowed(
            identifier, max_requests, window
        )
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {path}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again in {window} seconds.",
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + window)),
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time() + window)
        )
        
        return response


def setup_rate_limiting(app, enabled: bool = True):
    """Add rate limiting middleware to FastAPI app.
    
    Args:
        app: FastAPI application
        enabled: Whether to enable rate limiting (disable in development)
    """
    app.add_middleware(RateLimitMiddleware, enabled=enabled)
    
    if enabled:
        logger.info("✅ Rate limiting enabled")
    else:
        logger.info("⚠️ Rate limiting disabled (development mode)")
