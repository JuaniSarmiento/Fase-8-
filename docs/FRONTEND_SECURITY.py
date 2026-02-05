"""
Frontend Security Enhancements
================================

This file contains recommended security improvements for the Next.js frontend.
Implement these before production deployment.
"""

# ==================== 1. Environment Variables ====================

"""
Create .env.production file with production values:

NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_ENVIRONMENT=production
"""

# DO NOT expose sensitive keys in NEXT_PUBLIC_ variables!
# Only backend URLs and non-sensitive config should be public


# ==================== 2. Secure Token Storage ====================

"""
Current: localStorage (vulnerable to XSS)
Recommended: HttpOnly cookies (immune to XSS)

Implementation:
1. Backend: Set access token in HttpOnly cookie
2. Frontend: Remove token from localStorage
3. API calls: Cookies sent automatically

Example backend change (auth_router.py):

from fastapi import Response

@router.post("/login")
async def login(payload: LoginRequest, response: Response):
    # ... existing code ...
    
    # Set HttpOnly cookie instead of returning token
    response.set_cookie(
        key="access_token",
        value=f"Bearer {tokens['access_token']}",
        httponly=True,
        secure=True,  # HTTPS only
        samesite="strict",
        max_age=1800,  # 30 minutes
    )
    
    return UserWithTokensResponse(user=..., tokens=tokens)
"""


# ==================== 3. Content Security Policy ====================

"""
Add CSP meta tag in app/layout.tsx or use Next.js middleware:

// app/layout.tsx
export const metadata = {
  other: {
    'Content-Security-Policy': `
      default-src 'self';
      script-src 'self' 'unsafe-inline' 'unsafe-eval';
      style-src 'self' 'unsafe-inline';
      img-src 'self' data: https:;
      font-src 'self' data:;
      connect-src 'self' https://api.yourdomain.com;
      frame-ancestors 'none';
    `.replace(/\s+/g, ' ').trim()
  }
}

Or use middleware.ts:

// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const response = NextResponse.next()
  
  response.headers.set(
    'Content-Security-Policy',
    "default-src 'self'; ..."
  )
  
  return response
}
"""


# ==================== 4. XSS Protection ====================

"""
React provides automatic XSS protection, but verify:

1. NO dangerouslySetInnerHTML usage (already checked ✓)
2. Sanitize all user inputs before display
3. Use DOMPurify for rich text if needed:

npm install dompurify
npm install --save-dev @types/dompurify

import DOMPurify from 'dompurify';

function SafeHTML({ html }: { html: string }) {
  const clean = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}
"""


# ==================== 5. API Client Security ====================

"""
Update lib/api.ts with security improvements:

import axios, { AxiosError } from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 10000,  // 10 second timeout
  withCredentials: true,  // Send cookies with requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for CSRF token
api.interceptors.request.use((config) => {
  // Get CSRF token from meta tag or cookie
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  if (csrfToken) {
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
"""


# ==================== 6. Input Validation ====================

"""
Add client-side validation with Zod:

npm install zod

// lib/validation.ts
import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

export const codeSchema = z.object({
  code: z.string()
    .max(10000, 'Code is too long')
    .refine(
      (code) => !code.includes('<script>'),
      'Invalid code content'
    ),
});

// Usage in component
import { loginSchema } from '@/lib/validation';

function LoginForm() {
  const handleSubmit = (data: any) => {
    const result = loginSchema.safeParse(data);
    if (!result.success) {
      // Show validation errors
      console.error(result.error);
      return;
    }
    // Proceed with valid data
  };
}
"""


# ==================== 7. Rate Limiting on Frontend ====================

"""
Implement client-side rate limiting to prevent abuse:

// lib/rate-limiter.ts
class RateLimiter {
  private attempts: Map<string, number[]> = new Map();
  
  canProceed(key: string, maxAttempts: number, windowMs: number): boolean {
    const now = Date.now();
    const attempts = this.attempts.get(key) || [];
    
    // Remove old attempts
    const validAttempts = attempts.filter(time => now - time < windowMs);
    
    if (validAttempts.length >= maxAttempts) {
      return false;
    }
    
    validAttempts.push(now);
    this.attempts.set(key, validAttempts);
    return true;
  }
}

export const rateLimiter = new RateLimiter();

// Usage
if (!rateLimiter.canProceed('login', 5, 60000)) {
  toast.error('Too many attempts. Please wait.');
  return;
}
"""


# ==================== 8. Secure Form Submissions ====================

"""
Always validate and sanitize form data:

// components/forms/secure-form.tsx
import { FormEvent, useState } from 'react';

function SecureForm() {
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    // Prevent double submission
    if (loading) return;
    setLoading(true);
    
    try {
      const formData = new FormData(e.currentTarget);
      const data = Object.fromEntries(formData);
      
      // Validate with Zod
      const validated = schema.parse(data);
      
      // Submit to API
      await api.post('/endpoint', validated);
      
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button type="submit" disabled={loading}>
        {loading ? 'Submitting...' : 'Submit'}
      </button>
    </form>
  );
}
"""


# ==================== 9. Secure Code Editor ====================

"""
Monaco Editor security considerations:

// components/code-editor.tsx
import Editor from '@monaco-editor/react';

function SecureCodeEditor({ value, onChange }: Props) {
  const options = {
    // Disable eval-based features
    disableMonaco: false,
    
    // Security options
    readOnly: false,
    domReadOnly: false,
    
    // Resource limits
    maxTokenizationLineLength: 1000,
    
    // Validation
    validate: true,
  };
  
  const handleChange = (newValue: string | undefined) => {
    // Limit code size
    if (newValue && newValue.length > 50000) {
      toast.error('Code is too long');
      return;
    }
    
    onChange?.(newValue || '');
  };
  
  return (
    <Editor
      value={value}
      onChange={handleChange}
      options={options}
      // ... other props
    />
  );
}
"""


# ==================== 10. Protect Against CSRF ====================

"""
Implement CSRF token for state-changing operations:

// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { randomBytes } from 'crypto';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();
  
  // Generate CSRF token
  if (!request.cookies.get('csrf_token')) {
    const token = randomBytes(32).toString('hex');
    response.cookies.set('csrf_token', token, {
      httpOnly: true,
      secure: true,
      sameSite: 'strict',
    });
  }
  
  // Verify CSRF token for POST/PUT/DELETE
  if (['POST', 'PUT', 'DELETE'].includes(request.method)) {
    const cookieToken = request.cookies.get('csrf_token')?.value;
    const headerToken = request.headers.get('X-CSRF-Token');
    
    if (cookieToken !== headerToken) {
      return NextResponse.json(
        { error: 'Invalid CSRF token' },
        { status: 403 }
      );
    }
  }
  
  return response;
}
"""


# ==================== 11. Dependency Security ====================

"""
Regular security audits:

# Check for vulnerabilities
npm audit

# Fix automatically where possible
npm audit fix

# Update dependencies
npm update

# Check for outdated packages
npm outdated

# Use Snyk or similar for continuous monitoring
npm install -g snyk
snyk test
"""


# ==================== 12. Production Build Optimizations ====================

"""
// next.config.js
module.exports = {
  reactStrictMode: true,
  
  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          }
        ]
      }
    ];
  },
  
  // Remove source maps in production
  productionBrowserSourceMaps: false,
  
  // Optimize images
  images: {
    domains: ['yourdomain.com'],
    formats: ['image/avif', 'image/webp'],
  },
  
  // Compress
  compress: true,
  
  // Disable powered by header
  poweredByHeader: false,
};
"""


# ==================== Implementation Checklist ====================

"""
Frontend Security Checklist:

□ Move from localStorage to HttpOnly cookies
□ Implement Content Security Policy
□ Add input validation with Zod
□ Implement rate limiting on sensitive actions
□ Add CSRF protection
□ Configure security headers in next.config.js
□ Remove console.logs in production
□ Audit and update dependencies
□ Test with security tools (OWASP ZAP, etc.)
□ Enable HTTPS only in production
□ Implement error boundaries
□ Add loading states to prevent race conditions
□ Validate file uploads (type, size)
□ Implement proper logout (clear all auth state)
□ Add session timeout warning
□ Test with different browsers
□ Mobile security testing
□ Performance testing
□ Accessibility testing
□ SEO optimization
"""
