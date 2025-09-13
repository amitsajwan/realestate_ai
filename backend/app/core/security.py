"""
Security Enhancements
====================
Comprehensive security features for the Real Estate Platform
"""

import hashlib
import secrets
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from functools import wraps
import re
import ipaddress

from fastapi import Request, HTTPException, status
from fastapi.responses import Response
import jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting storage
rate_limit_storage = {}
failed_login_attempts = {}


class SecurityHeaders:
    """Security headers management"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get comprehensive security headers"""
        return {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # XSS Protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.facebook.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # Permissions Policy
            "Permissions-Policy": (
                "camera=(), "
                "microphone=(), "
                "geolocation=(), "
                "interest-cohort=()"
            ),
            
            # Cross-Origin Policies
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }
    
    @staticmethod
    def get_hsts_headers() -> Dict[str, str]:
        """Get HSTS headers for HTTPS"""
        return {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"
        }


class InputValidator:
    """Input validation and sanitization"""
    
    # Common patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?[\d\s\-\(\)]{10,}$')
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9]+$')
    SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?@#$%&*()+=\[\]{}|\\:";\'<>/]+$')
    
    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
        r'(\b(OR|AND)\s+\w+\s*=\s*\w+)',
        r'(\b(OR|AND)\s+\w+\s*LIKE\s*[\'"])',
        r'(\bUNION\s+SELECT\b)',
        r'(\bDROP\s+TABLE\b)',
        r'(\bDELETE\s+FROM\b)',
        r'(\bINSERT\s+INTO\b)',
        r'(\bUPDATE\s+SET\b)',
        r'(\bALTER\s+TABLE\b)',
    ]
    
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<link[^>]*>.*?</link>',
        r'<meta[^>]*>.*?</meta>',
    ]
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format"""
        if not email or len(email) > 254:
            return False
        return bool(cls.EMAIL_PATTERN.match(email))
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """Validate phone number format"""
        if not phone or len(phone) > 20:
            return False
        return bool(cls.PHONE_PATTERN.match(phone))
    
    @classmethod
    def validate_password_strength(cls, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    @classmethod
    def sanitize_string(cls, text: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not text:
            return ""
        
        # Truncate if too long
        text = text[:max_length]
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Check for dangerous patterns
        for pattern in cls.SQL_INJECTION_PATTERNS + cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Potentially dangerous input detected: {pattern}")
                # Remove or escape dangerous content
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @classmethod
    def validate_file_upload(cls, filename: str, content_type: str, file_size: int) -> Tuple[bool, str]:
        """Validate file upload"""
        # Check file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx'}
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            return False, f"File type {file_ext} not allowed"
        
        # Check content type
        allowed_content_types = {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        if content_type not in allowed_content_types:
            return False, f"Content type {content_type} not allowed"
        
        # Check file size (10MB max)
        max_size = 10 * 1024 * 1024
        if file_size > max_size:
            return False, f"File size {file_size} exceeds maximum {max_size} bytes"
        
        return True, "File upload valid"


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.requests = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_rate_limited(self, identifier: str, limit: int = 100, window: int = 60) -> bool:
        """Check if request is rate limited"""
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries()
            self.last_cleanup = current_time
        
        # Get or create request history for this identifier
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside the window
        cutoff_time = current_time - window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= limit:
            return True
        
        # Add current request
        self.requests[identifier].append(current_time)
        return False
    
    def _cleanup_old_entries(self):
        """Clean up old rate limiting entries"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # 1 hour
        
        to_remove = []
        for identifier, requests in self.requests.items():
            if not requests or max(requests) < cutoff_time:
                to_remove.append(identifier)
        
        for identifier in to_remove:
            del self.requests[identifier]
    
    def get_remaining_requests(self, identifier: str, limit: int = 100, window: int = 60) -> int:
        """Get remaining requests for an identifier"""
        current_time = time.time()
        cutoff_time = current_time - window
        
        if identifier not in self.requests:
            return limit
        
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]
        
        return max(0, limit - len(recent_requests))


class BruteForceProtection:
    """Brute force attack protection"""
    
    def __init__(self):
        self.max_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.failed_attempts = {}
    
    def record_failed_attempt(self, identifier: str) -> bool:
        """Record a failed login attempt"""
        current_time = time.time()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        # Remove old attempts outside lockout duration
        cutoff_time = current_time - self.lockout_duration
        self.failed_attempts[identifier] = [
            attempt_time for attempt_time in self.failed_attempts[identifier]
            if attempt_time > cutoff_time
        ]
        
        # Add current attempt
        self.failed_attempts[identifier].append(current_time)
        
        # Check if account should be locked
        return len(self.failed_attempts[identifier]) >= self.max_attempts
    
    def is_locked(self, identifier: str) -> bool:
        """Check if account is locked due to brute force attempts"""
        current_time = time.time()
        
        if identifier not in self.failed_attempts:
            return False
        
        # Remove old attempts
        cutoff_time = current_time - self.lockout_duration
        self.failed_attempts[identifier] = [
            attempt_time for attempt_time in self.failed_attempts[identifier]
            if attempt_time > cutoff_time
        ]
        
        return len(self.failed_attempts[identifier]) >= self.max_attempts
    
    def clear_failed_attempts(self, identifier: str):
        """Clear failed attempts for successful login"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]


class SecurityMiddleware:
    """Security middleware for FastAPI"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.brute_force_protection = BruteForceProtection()
    
    async def __call__(self, request: Request, call_next):
        """Process request through security middleware"""
        start_time = time.time()
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        identifier = f"{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
        
        # Check rate limiting
        if self.rate_limiter.is_rate_limited(identifier):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Check brute force protection for auth endpoints
        if request.url.path.startswith("/api/v1/auth/"):
            if self.brute_force_protection.is_locked(identifier):
                logger.warning(f"Account locked due to brute force attempts: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account temporarily locked due to multiple failed attempts"
                )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Record failed attempt for auth endpoints
            if request.url.path.startswith("/api/v1/auth/login"):
                self.brute_force_protection.record_failed_attempt(identifier)
            raise
        
        # Add security headers
        for header, value in SecurityHeaders.get_security_headers().items():
            response.headers[header] = value
        
        # Add HSTS headers for HTTPS
        if request.url.scheme == "https":
            for header, value in SecurityHeaders.get_hsts_headers().items():
                response.headers[header] = value
        
        # Add rate limit headers
        remaining = self.rate_limiter.get_remaining_requests(identifier)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        # Log request
        duration = time.time() - start_time
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} - {response.status_code} - {duration:.3f}s"
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


# Global instances
rate_limiter = RateLimiter()
brute_force_protection = BruteForceProtection()
security_middleware = SecurityMiddleware()


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


def generate_csrf_token() -> str:
    """Generate a CSRF token"""
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, session_token: str) -> bool:
    """Validate CSRF token"""
    return secrets.compare_digest(token, session_token)


def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    return InputValidator.sanitize_string(text)


def validate_email(email: str) -> bool:
    """Validate email address"""
    return InputValidator.validate_email(email)


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """Validate password strength"""
    return InputValidator.validate_password_strength(password)


def validate_file_upload(filename: str, content_type: str, file_size: int) -> Tuple[bool, str]:
    """Validate file upload"""
    return InputValidator.validate_file_upload(filename, content_type, file_size)


def is_rate_limited(identifier: str, limit: int = 100, window: int = 60) -> bool:
    """Check if request is rate limited"""
    return rate_limiter.is_rate_limited(identifier, limit, window)


def record_failed_login(identifier: str) -> bool:
    """Record a failed login attempt"""
    return brute_force_protection.record_failed_attempt(identifier)


def is_account_locked(identifier: str) -> bool:
    """Check if account is locked"""
    return brute_force_protection.is_locked(identifier)


def clear_failed_logins(identifier: str):
    """Clear failed login attempts"""
    brute_force_protection.clear_failed_attempts(identifier)