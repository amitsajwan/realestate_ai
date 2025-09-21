"""
Security Hardening and Best Practices
====================================
Production-ready security measures
"""

import secrets
import hashlib
import hmac
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import re
import ipaddress
from urllib.parse import urlparse

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key-change-in-production"  # Should be from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Rate limiting
RATE_LIMIT_STORE = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100

# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
}

class SecurityManager:
    """Centralized security management"""
    
    def __init__(self):
        self.blocked_ips = set()
        self.suspicious_ips = {}
        self.failed_attempts = {}
        self.max_failed_attempts = 5
        self.lockout_duration = 300  # 5 minutes
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit"""
        current_time = time.time()
        
        # Clean old entries
        if client_ip in RATE_LIMIT_STORE:
            RATE_LIMIT_STORE[client_ip] = [
                timestamp for timestamp in RATE_LIMIT_STORE[client_ip]
                if current_time - timestamp < RATE_LIMIT_WINDOW
            ]
        else:
            RATE_LIMIT_STORE[client_ip] = []
        
        # Check if limit exceeded
        if len(RATE_LIMIT_STORE[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return False
        
        # Add current request
        RATE_LIMIT_STORE[client_ip].append(current_time)
        return True
    
    def is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is blocked"""
        return client_ip in self.blocked_ips
    
    def block_ip(self, client_ip: str, reason: str = "Suspicious activity"):
        """Block an IP address"""
        self.blocked_ips.add(client_ip)
        # Log security event
        print(f"IP {client_ip} blocked: {reason}")
    
    def record_failed_attempt(self, client_ip: str, user_id: str = None):
        """Record failed login attempt"""
        key = f"{client_ip}:{user_id or 'unknown'}"
        current_time = time.time()
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = []
        
        # Clean old attempts
        self.failed_attempts[key] = [
            timestamp for timestamp in self.failed_attempts[key]
            if current_time - timestamp < self.lockout_duration
        ]
        
        # Add current attempt
        self.failed_attempts[key].append(current_time)
        
        # Check if should be blocked
        if len(self.failed_attempts[key]) >= self.max_failed_attempts:
            self.block_ip(client_ip, f"Too many failed attempts for {key}")
    
    def is_locked_out(self, client_ip: str, user_id: str = None) -> bool:
        """Check if client is locked out"""
        key = f"{client_ip}:{user_id or 'unknown'}"
        if key not in self.failed_attempts:
            return False
        
        current_time = time.time()
        recent_attempts = [
            timestamp for timestamp in self.failed_attempts[key]
            if current_time - timestamp < self.lockout_duration
        ]
        
        return len(recent_attempts) >= self.max_failed_attempts
    
    def validate_input(self, input_data: str, input_type: str = "general") -> bool:
        """Validate user input for security"""
        if not input_data:
            return False
        
        # SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+'.*'\s*=\s*'.*')",
            r"(--|\#|\/\*|\*\/)",
            r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT)\b)",
        ]
        
        # XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
        ]
        
        # Command injection patterns
        cmd_patterns = [
            r"[;&|`$]",
            r"\b(rm|del|mkdir|rmdir|cat|ls|dir|type|copy|move)\b",
            r"\.\.\/",
            r"\.\.\\\\",
        ]
        
        all_patterns = sql_patterns + xss_patterns + cmd_patterns
        
        for pattern in all_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                return False
        
        return True
    
    def sanitize_input(self, input_data: str) -> str:
        """Sanitize user input"""
        if not input_data:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r"[<>\"'%;()&+]", "", input_data)
        
        # Limit length
        sanitized = sanitized[:1000]
        
        return sanitized.strip()
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        result = {
            "valid": True,
            "score": 0,
            "issues": []
        }
        
        if len(password) < 8:
            result["valid"] = False
            result["issues"].append("Password must be at least 8 characters long")
        else:
            result["score"] += 1
        
        if not re.search(r"[a-z]", password):
            result["issues"].append("Password must contain lowercase letters")
        else:
            result["score"] += 1
        
        if not re.search(r"[A-Z]", password):
            result["issues"].append("Password must contain uppercase letters")
        else:
            result["score"] += 1
        
        if not re.search(r"\d", password):
            result["issues"].append("Password must contain numbers")
        else:
            result["score"] += 1
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            result["issues"].append("Password must contain special characters")
        else:
            result["score"] += 1
        
        if result["score"] < 3:
            result["valid"] = False
        
        return result
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def verify_csrf_token(self, token: str, session_token: str) -> bool:
        """Verify CSRF token"""
        return hmac.compare_digest(token, session_token)
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def is_safe_redirect_url(self, url: str, allowed_domains: List[str] = None) -> bool:
        """Check if redirect URL is safe"""
        if not self.is_valid_url(url):
            return False
        
        parsed = urlparse(url)
        
        # Check if it's a relative URL
        if not parsed.netloc:
            return True
        
        # Check against allowed domains
        if allowed_domains:
            return parsed.netloc in allowed_domains
        
        # Default: only allow same-origin redirects
        return False

# Global security manager instance
security_manager = SecurityManager()

class SecurityMiddleware:
    """Security middleware for FastAPI"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Get client IP
        client_ip = security_manager.get_client_ip(request)
        
        # Check if IP is blocked
        if security_manager.is_ip_blocked(client_ip):
            response = JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Access denied"}
            )
            await response(scope, receive, send)
            return
        
        # Check rate limit
        if not security_manager.check_rate_limit(client_ip):
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded"}
            )
            await response(scope, receive, send)
            return
        
        # Add security headers
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for header, value in SECURITY_HEADERS.items():
                    headers.append([header.encode(), value.encode()])
                message["headers"] = headers
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

def get_security_headers() -> Dict[str, str]:
    """Get security headers"""
    return SECURITY_HEADERS.copy()

def validate_request_security(request: Request) -> bool:
    """Validate request for security issues"""
    client_ip = security_manager.get_client_ip(request)
    
    # Check if IP is blocked
    if security_manager.is_ip_blocked(client_ip):
        return False
    
    # Check rate limit
    if not security_manager.check_rate_limit(client_ip):
        return False
    
    return True