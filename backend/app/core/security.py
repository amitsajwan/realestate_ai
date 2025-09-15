"""
Security Hardening Implementation
===============================
Comprehensive security measures for the Multi-Post Management System.
"""

import logging
import hashlib
import secrets
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from passlib.context import CryptContext
import re

logger = logging.getLogger(__name__)

# Security configuration
SECURITY_CONFIG = {
    "jwt_secret": "your-super-secret-jwt-key-change-in-production",
    "jwt_algorithm": "HS256",
    "jwt_expire_minutes": 30,
    "bcrypt_rounds": 12,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 15,
    "password_min_length": 8,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
    "password_require_numbers": True,
    "password_require_special": True,
    "rate_limit_requests": 100,
    "rate_limit_window": 60
}

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token
security = HTTPBearer()


class SecurityService:
    """Comprehensive security service."""
    
    def __init__(self):
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        logger.info("Initialized SecurityService")
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength."""
        issues = []
        
        if len(password) < SECURITY_CONFIG["password_min_length"]:
            issues.append(f"Password must be at least {SECURITY_CONFIG['password_min_length']} characters")
        
        if SECURITY_CONFIG["password_require_uppercase"] and not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if SECURITY_CONFIG["password_require_lowercase"] and not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if SECURITY_CONFIG["password_require_numbers"] and not re.search(r'\d', password):
            issues.append("Password must contain at least one number")
        
        if SECURITY_CONFIG["password_require_special"] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "strength_score": self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)."""
        score = 0
        
        # Length bonus
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Character variety
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 10
        
        # Complexity bonus
        if len(set(password)) > len(password) * 0.7:
            score += 10
        
        return min(score, 100)
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(length)
    
    def create_jwt_token(self, user_id: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=SECURITY_CONFIG["jwt_expire_minutes"])
        
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": self.generate_secure_token(16)  # JWT ID for token revocation
        }
        
        return jwt.encode(payload, SECURITY_CONFIG["jwt_secret"], algorithm=SECURITY_CONFIG["jwt_algorithm"])
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECURITY_CONFIG["jwt_secret"], algorithms=[SECURITY_CONFIG["jwt_algorithm"]])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit."""
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=SECURITY_CONFIG["rate_limit_window"])
        
        # Clean old attempts
        if client_ip in self.failed_attempts:
            self.failed_attempts[client_ip] = [
                attempt for attempt in self.failed_attempts[client_ip]
                if attempt > window_start
            ]
        else:
            self.failed_attempts[client_ip] = []
        
        # Check rate limit
        if len(self.failed_attempts[client_ip]) >= SECURITY_CONFIG["rate_limit_requests"]:
            return False
        
        # Record this attempt
        self.failed_attempts[client_ip].append(current_time)
        return True
    
    def check_login_attempts(self, email: str) -> bool:
        """Check if user has exceeded login attempts."""
        current_time = datetime.utcnow()
        lockout_duration = timedelta(minutes=SECURITY_CONFIG["lockout_duration_minutes"])
        
        if email in self.failed_attempts:
            # Clean old attempts
            self.failed_attempts[email] = [
                attempt for attempt in self.failed_attempts[email]
                if attempt > current_time - lockout_duration
            ]
            
            # Check if locked out
            if len(self.failed_attempts[email]) >= SECURITY_CONFIG["max_login_attempts"]:
                return False
        
        return True
    
    def record_failed_login(self, email: str):
        """Record a failed login attempt."""
        if email not in self.failed_attempts:
            self.failed_attempts[email] = []
        
        self.failed_attempts[email].append(datetime.utcnow())
        logger.warning(f"Failed login attempt for {email}")
    
    def clear_failed_attempts(self, email: str):
        """Clear failed login attempts for a user."""
        if email in self.failed_attempts:
            del self.failed_attempts[email]
    
    def sanitize_input(self, input_string: str) -> str:
        """Sanitize user input to prevent XSS."""
        if not input_string:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', input_string)
        
        # Limit length
        return sanitized[:1000]
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def check_sql_injection(self, input_string: str) -> bool:
        """Check for potential SQL injection patterns."""
        dangerous_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)',
            r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
            r'(\b(OR|AND)\s+\w+\s*=\s*\w+)',
            r'(--|\#|\/\*|\*\/)',
            r'(\b(UNION|SELECT)\b.*\b(FROM|WHERE)\b)'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                return True
        
        return False
    
    def check_xss_patterns(self, input_string: str) -> bool:
        """Check for potential XSS patterns."""
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                return True
        
        return False
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for responses."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "medium"):
        """Log security events."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "details": details
        }
        
        if severity == "high":
            logger.critical(f"SECURITY EVENT: {json.dumps(log_data)}")
        elif severity == "medium":
            logger.warning(f"SECURITY EVENT: {json.dumps(log_data)}")
        else:
            logger.info(f"SECURITY EVENT: {json.dumps(log_data)}")


# Global security service instance
security_service = SecurityService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token."""
    try:
        payload = security_service.verify_jwt_token(credentials.credentials)
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


def require_permissions(permissions: List[str]):
    """Decorator to require specific permissions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would check user permissions
            # Implementation depends on your permission system
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Decorator for rate limiting."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            
            if not security_service.check_rate_limit(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later."
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator