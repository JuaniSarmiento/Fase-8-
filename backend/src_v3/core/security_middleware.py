"""Security Middleware for HTTP Headers and Protection.

Implements:
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Request/Response logging
- Attack pattern detection
"""
from __future__ import annotations

import logging
import re
from typing import Set
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Strict Transport Security (HSTS)
        # Force HTTPS for 1 year, include subdomains
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy (CSP)
        # Prevent XSS attacks
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow inline scripts for dev
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' http://localhost:* https://*",
            "frame-ancestors 'none'",  # Prevent clickjacking
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # X-Frame-Options: Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options: Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection: Enable browser XSS filter
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy: Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy: Disable unnecessary browser features
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)
        
        # Remove server identification
        response.headers.pop("Server", None)
        
        return response


class SQLInjectionDetector(BaseHTTPMiddleware):
    """Detect and block potential SQL injection attempts."""
    
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bor\b\s+\d+\s*=\s*\d+)",
        r"(\band\b\s+\d+\s*=\s*\d+)",
        r"(';?\s*(drop|delete|insert|update|exec|execute)\b)",
        r"(\bexec\s*\()",
        r"(\bselect\b.*\bfrom\b.*\bwhere\b)",
        r"(--|\#|\/\*|\*\/)",  # SQL comments
    ]
    
    def __init__(self, app):
        super().__init__(app)
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SQL_INJECTION_PATTERNS]
    
    def _check_sql_injection(self, text: str) -> bool:
        """Check if text contains SQL injection patterns."""
        for pattern in self.patterns:
            if pattern.search(text):
                return True
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Check request for SQL injection patterns."""
        # Check query parameters
        query_string = str(request.url.query)
        if self._check_sql_injection(query_string):
            logger.warning(
                f"SQL injection attempt detected from {request.client.host}: {query_string}"
            )
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request parameters"}
            )
        
        # Check path parameters
        if self._check_sql_injection(request.url.path):
            logger.warning(
                f"SQL injection attempt in path from {request.client.host}: {request.url.path}"
            )
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request path"}
            )
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for security monitoring."""
    
    SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key"}
    SENSITIVE_PATHS = {"/api/v3/auth/login", "/api/v3/auth/register"}
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response."""
        # Log request
        client_host = request.client.host if request.client else "unknown"
        
        # Filter sensitive headers
        headers_to_log = {
            k: v for k, v in request.headers.items()
            if k.lower() not in self.SENSITIVE_HEADERS
        }
        
        logger.info(
            f"Request: {request.method} {request.url.path} from {client_host}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": client_host,
                "headers": headers_to_log,
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} -> {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "client": client_host,
            }
        )
        
        return response


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """Detect and block potential XSS attacks."""
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
        r"<iframe[^>]*>",
        r"eval\s*\(",
        r"expression\s*\(",
    ]
    
    def __init__(self, app):
        super().__init__(app)
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.XSS_PATTERNS]
        # Exempt paths where code is expected (exercise submissions)
        self.exempt_paths: Set[str] = {
            "/api/v3/student/activities/",  # Exercise submissions contain code
            "/api/v3/teacher/activities/",   # Activity creation with code
        }
    
    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from XSS checking."""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    def _check_xss(self, text: str) -> bool:
        """Check if text contains XSS patterns."""
        for pattern in self.patterns:
            if pattern.search(text):
                return True
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Check request for XSS patterns."""
        # Skip exempt paths
        if self._is_exempt(request.url.path):
            return await call_next(request)
        
        # Check query parameters
        query_string = str(request.url.query)
        if self._check_xss(query_string):
            logger.warning(
                f"XSS attempt detected from {request.client.host}: {query_string}"
            )
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request parameters"}
            )
        
        return await call_next(request)
