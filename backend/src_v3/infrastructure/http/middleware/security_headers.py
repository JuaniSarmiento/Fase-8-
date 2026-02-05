"""Security Headers Middleware for Production.

Adds security headers to all HTTP responses to protect against common attacks.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    def __init__(self, app, enable_hsts: bool = True):
        super().__init__(app)
        self.enable_hsts = enable_hsts
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Strict Transport Security (HTTPS only)
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        # X-Frame-Options (prevent clickjacking)
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options (prevent MIME sniffing)
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        # Remove Server header (don't reveal tech stack)
        if "Server" in response.headers:
            del response.headers["Server"]
        
        return response


def setup_security_headers(app, enable_hsts: bool = False):
    """Add security headers middleware to FastAPI app.
    
    Args:
        app: FastAPI application
        enable_hsts: Enable HSTS (only in production with HTTPS)
    """
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=enable_hsts)
    logger.info(f"✅ Security headers enabled (HSTS: {enable_hsts})")
