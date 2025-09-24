"""
Enhanced Security Manager
=========================
Centralized security management with comprehensive features
"""

import secrets
import hashlib
import hmac
import time
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import re
import ipaddress
from urllib.parse import urlparse
import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
}


class SecurityConfig:
    """Security configuration class"""
    
    def __init__(self):
        self.jwt_secret_key = settings.jwt_secret_key
        self.jwt_algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
        
        # Rate limiting
        self.rate_limit_requests = settings.rate_limit_requests
        self.rate_limit_window = settings.rate_limit_window
        
        # Security thresholds
        self.max_failed_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        self.suspicious_activity_threshold = 10
        
        # Redis settings
        self.redis_url = settings.redis_url
        self.redis_password = settings.redis_password
        self.redis_db = settings.redis_db


class SecurityResult:
    """Security validation result"""
    
    def __init__(self, allowed: bool, reason: str = None, retry_after: int = None):
        self.allowed = allowed
        self.reason = reason
        self.retry_after = retry_after


class RateLimiter:
    """Intelligent rate limiter with Redis backend"""
    
    def __init__(self, redis_client: redis.Redis, config: SecurityConfig):
        self.redis = redis_client
        self.config = config
    
    async def check_rate_limit(self, client_ip: str, endpoint: str = None) -> SecurityResult:
        """Check if client has exceeded rate limit"""
        try:
            # Create rate limit key
            key = f"rate_limit:{client_ip}:{endpoint or 'global'}"
            
            # Get current count
            current_count = await self.redis.get(key)
            current_count = int(current_count) if current_count else 0
            
            # Check if limit exceeded
            if current_count >= self.config.rate_limit_requests:
                # Get TTL for retry_after
                ttl = await self.redis.ttl(key)
                return SecurityResult(
                    allowed=False,
                    reason="Rate limit exceeded",
                    retry_after=ttl if ttl > 0 else self.config.rate_limit_window
                )
            
            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.config.rate_limit_window)
            await pipe.execute()
            
            return SecurityResult(allowed=True)
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Fail open - allow request if Redis is down
            return SecurityResult(allowed=True)
    
    async def is_suspicious_pattern(self, request: Request) -> bool:
        """Detect suspicious request patterns"""
        try:
            # Check for rapid requests to different endpoints
            client_ip = self.get_client_ip(request)
            pattern_key = f"suspicious:{client_ip}"
            
            # Track endpoint access patterns
            endpoint = request.url.path
            timestamp = time.time()
            
            # Store endpoint access
            await self.redis.zadd(pattern_key, {endpoint: timestamp})
            await self.redis.expire(pattern_key, 60)  # 1 minute window
            
            # Check for rapid endpoint switching
            recent_endpoints = await self.redis.zrange(pattern_key, -10, -1)
            unique_endpoints = set(recent_endpoints)
            
            # If accessing many different endpoints rapidly, it's suspicious
            if len(unique_endpoints) > 5:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Suspicious pattern detection error: {e}")
            return False
    
    async def increase_suspicion(self, client_ip: str, reason: str = "Suspicious activity"):
        """Increase suspicion level for an IP"""
        try:
            suspicion_key = f"suspicion:{client_ip}"
            current_level = await self.redis.incr(suspicion_key)
            await self.redis.expire(suspicion_key, 3600)  # 1 hour
            
            # Log suspicious activity
            logger.warning(f"Suspicious activity from {client_ip}: {reason} (level: {current_level})")
            
            # Block if suspicion level is too high
            if current_level >= self.config.suspicious_activity_threshold:
                await self.block_ip(client_ip, f"High suspicion level: {current_level}")
                
        except Exception as e:
            logger.error(f"Error increasing suspicion for {client_ip}: {e}")


class CORSManager:
    """Dynamic CORS management"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.allowed_origins = set(settings.cors_origins)
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed"""
        if not origin:
            return False
        
        # Check exact match
        if origin in self.allowed_origins:
            return True
        
        # Check wildcard subdomains
        for allowed_origin in self.allowed_origins:
            if allowed_origin.startswith("*."):
                domain = allowed_origin[2:]
                if origin.endswith(domain):
                    return True
        
        return False
    
    def add_origin(self, origin: str):
        """Add new allowed origin"""
        self.allowed_origins.add(origin)
    
    def remove_origin(self, origin: str):
        """Remove allowed origin"""
        self.allowed_origins.discard(origin)


class SecurityValidator:
    """Comprehensive input validation"""
    
    @staticmethod
    def validate_and_sanitize(input_data: str, input_type: str = "general") -> Tuple[bool, str]:
        """Validate and sanitize input data"""
        if not input_data:
            return False, "Input cannot be empty"
        
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
                return False, f"Potentially malicious pattern detected: {pattern}"
        
        # Sanitize input
        sanitized = re.sub(r"[<>\"'%;()&+]", "", input_data)
        sanitized = sanitized[:1000].strip()
        
        return True, sanitized
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
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


class EnhancedSecurityManager:
    """Enhanced centralized security management"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.redis_client = None
        self.rate_limiter = None
        self.cors_manager = CORSManager(config)
        self.validator = SecurityValidator()
        
        # In-memory fallback for blocked IPs
        self.blocked_ips = set()
        self.failed_attempts = {}
    
    async def initialize(self):
        """Initialize Redis connection and components"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                password=self.config.redis_password,
                db=self.config.redis_db,
                decode_responses=True
            )
            self.rate_limiter = RateLimiter(self.redis_client, self.config)
            logger.info("Enhanced Security Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            # Continue without Redis - will use in-memory fallback
    
    async def validate_request(self, request: Request) -> SecurityResult:
        """Unified security validation pipeline"""
        try:
            client_ip = self.get_client_ip(request)
            
            # Check if IP is blocked
            if await self.is_ip_blocked(client_ip):
                return SecurityResult(
                    allowed=False,
                    reason="IP address is blocked"
                )
            
            # Check rate limit
            rate_limit_result = await self.rate_limiter.check_rate_limit(
                client_ip, 
                request.url.path
            )
            if not rate_limit_result.allowed:
                return rate_limit_result
            
            # Check for suspicious patterns
            if await self.rate_limiter.is_suspicious_pattern(request):
                await self.rate_limiter.increase_suspicion(client_ip, "Suspicious request pattern")
                return SecurityResult(
                    allowed=False,
                    reason="Suspicious activity detected"
                )
            
            return SecurityResult(allowed=True)
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            # Fail open - allow request if security check fails
            return SecurityResult(allowed=True)
    
    async def handle_auth_failure(self, request: Request, reason: str, user_id: str = None):
        """Centralized security event handling"""
        try:
            client_ip = self.get_client_ip(request)
            
            # Record failed attempt
            await self.record_failed_attempt(client_ip, user_id)
            
            # Log security event
            logger.warning(f"Authentication failure: {reason} from {client_ip}")
            
            # Check if should block IP
            if await self.is_locked_out(client_ip, user_id):
                await self.block_ip(client_ip, f"Too many failed attempts: {reason}")
            
        except Exception as e:
            logger.error(f"Error handling auth failure: {e}")
    
    async def is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is blocked"""
        try:
            if self.redis_client:
                blocked = await self.redis_client.get(f"blocked:{client_ip}")
                return blocked is not None
            else:
                return client_ip in self.blocked_ips
        except Exception as e:
            logger.error(f"Error checking if IP is blocked: {e}")
            return client_ip in self.blocked_ips
    
    async def block_ip(self, client_ip: str, reason: str = "Suspicious activity"):
        """Block an IP address"""
        try:
            if self.redis_client:
                await self.redis_client.setex(
                    f"blocked:{client_ip}",
                    3600,  # Block for 1 hour
                    reason
                )
            else:
                self.blocked_ips.add(client_ip)
            
            logger.warning(f"IP {client_ip} blocked: {reason}")
        except Exception as e:
            logger.error(f"Error blocking IP {client_ip}: {e}")
    
    async def record_failed_attempt(self, client_ip: str, user_id: str = None):
        """Record failed login attempt"""
        try:
            key = f"{client_ip}:{user_id or 'unknown'}"
            current_time = time.time()
            
            if self.redis_client:
                # Use Redis for distributed tracking
                attempt_key = f"failed_attempts:{key}"
                await self.redis_client.lpush(attempt_key, current_time)
                await self.redis_client.expire(attempt_key, self.config.lockout_duration)
            else:
                # Fallback to in-memory
                if key not in self.failed_attempts:
                    self.failed_attempts[key] = []
                
                # Clean old attempts
                self.failed_attempts[key] = [
                    timestamp for timestamp in self.failed_attempts[key]
                    if current_time - timestamp < self.config.lockout_duration
                ]
                
                # Add current attempt
                self.failed_attempts[key].append(current_time)
                
        except Exception as e:
            logger.error(f"Error recording failed attempt: {e}")
    
    async def is_locked_out(self, client_ip: str, user_id: str = None) -> bool:
        """Check if client is locked out"""
        try:
            key = f"{client_ip}:{user_id or 'unknown'}"
            
            if self.redis_client:
                attempt_key = f"failed_attempts:{key}"
                attempts = await self.redis_client.lrange(attempt_key, 0, -1)
                return len(attempts) >= self.config.max_failed_attempts
            else:
                if key not in self.failed_attempts:
                    return False
                
                current_time = time.time()
                recent_attempts = [
                    timestamp for timestamp in self.failed_attempts[key]
                    if current_time - timestamp < self.config.lockout_duration
                ]
                
                return len(recent_attempts) >= self.config.max_failed_attempts
                
        except Exception as e:
            logger.error(f"Error checking lockout status: {e}")
            return False
    
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
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers"""
        return SECURITY_HEADERS.copy()
    
    async def cleanup_expired_data(self):
        """Clean up expired security data"""
        try:
            if self.redis_client:
                # Clean expired blocked IPs, failed attempts, etc.
                current_time = int(time.time())
                
                # This would be implemented based on specific Redis key patterns
                # For now, Redis TTL handles most cleanup automatically
                logger.info("Security data cleanup completed")
        except Exception as e:
            logger.error(f"Error during security cleanup: {e}")


# Global security manager instance
security_config = SecurityConfig()
security_manager = EnhancedSecurityManager(security_config)
