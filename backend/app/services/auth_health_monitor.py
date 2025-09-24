"""
Authentication Health Monitoring and Alerting
============================================
Comprehensive monitoring system for authentication components
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.services.token_lifecycle_manager import TokenLifecycleManager
from app.core.enhanced_security import EnhancedSecurityManager

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthCheck:
    """Individual health check result"""
    
    def __init__(self, name: str, status: HealthStatus, message: str = "", details: Dict[str, Any] = None):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        self.duration_ms = 0


class AuthHealthMonitor:
    """Authentication system health monitoring"""
    
    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        redis_client: redis.Redis,
        user_repository: UserRepository,
        token_manager: TokenLifecycleManager,
        security_manager: EnhancedSecurityManager
    ):
        self.database = database
        self.redis = redis_client
        self.user_repository = user_repository
        self.token_manager = token_manager
        self.security_manager = security_manager
        
        # Health check thresholds
        self.thresholds = {
            "response_time_ms": 1000,  # 1 second
            "error_rate_percent": 5.0,  # 5%
            "memory_usage_percent": 80.0,  # 80%
            "cpu_usage_percent": 80.0,  # 80%
            "active_connections": 1000,
            "failed_logins_per_minute": 10,
        }
        
        # Alerting configuration
        self.alerting_enabled = True
        self.alert_cooldown = 300  # 5 minutes
        self.last_alerts = {}
        
        # Health check history
        self.health_history = []
        self.max_history_size = 100
    
    async def check_auth_system_health(self) -> Dict[str, Any]:
        """Comprehensive authentication system health check"""
        start_time = time.time()
        
        try:
            # Run all health checks
            checks = await asyncio.gather(
                self._check_database_connectivity(),
                self._check_redis_connectivity(),
                self._check_token_generation(),
                self._check_oauth_providers(),
                self._check_rate_limiting(),
                self._check_security_systems(),
                self._check_user_management(),
                self._check_token_cleanup(),
                self._check_system_resources(),
                return_exceptions=True
            )
            
            # Process results
            health_checks = []
            for check in checks:
                if isinstance(check, Exception):
                    health_checks.append(HealthCheck(
                        name="system_error",
                        status=HealthStatus.CRITICAL,
                        message=f"Health check failed: {str(check)}"
                    ))
                else:
                    health_checks.append(check)
            
            # Calculate overall health status
            overall_status = self._calculate_overall_status(health_checks)
            
            # Store health check result
            health_result = {
                "status": overall_status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": int((time.time() - start_time) * 1000),
                "checks": [
                    {
                        "name": check.name,
                        "status": check.status.value,
                        "message": check.message,
                        "details": check.details,
                        "timestamp": check.timestamp.isoformat(),
                        "duration_ms": check.duration_ms
                    }
                    for check in health_checks
                ],
                "summary": self._generate_health_summary(health_checks)
            }
            
            # Store in history
            self._store_health_result(health_result)
            
            # Send alerts if needed
            if self.alerting_enabled:
                await self._check_and_send_alerts(health_result)
            
            return health_result
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": HealthStatus.CRITICAL.value,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "checks": []
            }
    
    async def _check_database_connectivity(self) -> HealthCheck:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            await self.database.admin.command('ping')
            
            # Test user collection access
            user_count = await self.database.users.count_documents({})
            
            # Test write performance
            test_doc = {"_health_check": datetime.utcnow()}
            result = await self.database.health_checks.insert_one(test_doc)
            await self.database.health_checks.delete_one({"_id": result.inserted_id})
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            status = HealthStatus.HEALTHY
            if duration_ms > self.thresholds["response_time_ms"]:
                status = HealthStatus.WARNING
            
            return HealthCheck(
                name="database_connectivity",
                status=status,
                message=f"Database connected successfully",
                details={
                    "response_time_ms": duration_ms,
                    "user_count": user_count,
                    "write_test": "passed"
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="database_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_redis_connectivity(self) -> HealthCheck:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            await self.redis.ping()
            
            # Test read/write performance
            test_key = f"health_check:{int(time.time())}"
            await self.redis.set(test_key, "test_value", ex=60)
            value = await self.redis.get(test_key)
            await self.redis.delete(test_key)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            status = HealthStatus.HEALTHY
            if duration_ms > self.thresholds["response_time_ms"]:
                status = HealthStatus.WARNING
            
            return HealthCheck(
                name="redis_connectivity",
                status=status,
                message="Redis connected successfully",
                details={
                    "response_time_ms": duration_ms,
                    "read_write_test": "passed" if value == "test_value" else "failed"
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="redis_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Redis connection failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_token_generation(self) -> HealthCheck:
        """Check token generation and validation"""
        start_time = time.time()
        
        try:
            # Test token generation
            test_user_id = "health_check_user"
            tokens = await self.token_manager.create_tokens(test_user_id)
            
            # Test token validation
            validation_result = await self.token_manager.validate_token(tokens.access_token)
            
            # Clean up test tokens
            await self.token_manager.revoke_all_user_tokens(test_user_id)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            status = HealthStatus.HEALTHY
            if not validation_result.valid:
                status = HealthStatus.CRITICAL
            elif duration_ms > self.thresholds["response_time_ms"]:
                status = HealthStatus.WARNING
            
            return HealthCheck(
                name="token_generation",
                status=status,
                message="Token generation and validation working",
                details={
                    "response_time_ms": duration_ms,
                    "token_validation": "passed" if validation_result.valid else "failed",
                    "token_type": validation_result.token_type
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="token_generation",
                status=HealthStatus.CRITICAL,
                message=f"Token generation failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_oauth_providers(self) -> HealthCheck:
        """Check OAuth provider connectivity"""
        start_time = time.time()
        
        try:
            # Check Facebook OAuth configuration
            facebook_configured = bool(settings.facebook_app_id and settings.facebook_app_secret)
            
            # Check Google OAuth configuration
            google_configured = bool(settings.google_client_id and settings.google_client_secret)
            
            # Check LinkedIn OAuth configuration
            linkedin_configured = bool(settings.linkedin_client_id and settings.linkedin_client_secret)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            configured_providers = sum([facebook_configured, google_configured, linkedin_configured])
            
            status = HealthStatus.HEALTHY
            if configured_providers == 0:
                status = HealthStatus.WARNING
                message = "No OAuth providers configured"
            else:
                message = f"{configured_providers} OAuth providers configured"
            
            return HealthCheck(
                name="oauth_providers",
                status=status,
                message=message,
                details={
                    "response_time_ms": duration_ms,
                    "facebook_configured": facebook_configured,
                    "google_configured": google_configured,
                    "linkedin_configured": linkedin_configured,
                    "total_configured": configured_providers
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="oauth_providers",
                status=HealthStatus.CRITICAL,
                message=f"OAuth provider check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_rate_limiting(self) -> HealthCheck:
        """Check rate limiting system"""
        start_time = time.time()
        
        try:
            # Test rate limiting functionality
            test_ip = "127.0.0.1"
            
            # Check if rate limiter is working
            result = await self.security_manager.rate_limiter.check_rate_limit(test_ip, "health_check")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            status = HealthStatus.HEALTHY
            if not result.allowed:
                status = HealthStatus.WARNING
                message = "Rate limiting is blocking requests"
            else:
                message = "Rate limiting system operational"
            
            return HealthCheck(
                name="rate_limiting",
                status=status,
                message=message,
                details={
                    "response_time_ms": duration_ms,
                    "rate_limit_allowed": result.allowed,
                    "rate_limit_reason": result.reason
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="rate_limiting",
                status=HealthStatus.CRITICAL,
                message=f"Rate limiting check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_security_systems(self) -> HealthCheck:
        """Check security systems"""
        start_time = time.time()
        
        try:
            # Check security manager initialization
            security_initialized = self.security_manager.redis_client is not None
            
            # Check blocked IPs
            blocked_ips_count = len(self.security_manager.blocked_ips)
            
            # Check failed attempts tracking
            failed_attempts_count = len(self.security_manager.failed_attempts)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            status = HealthStatus.HEALTHY
            if not security_initialized:
                status = HealthStatus.WARNING
                message = "Security manager not fully initialized"
            else:
                message = "Security systems operational"
            
            return HealthCheck(
                name="security_systems",
                status=status,
                message=message,
                details={
                    "response_time_ms": duration_ms,
                    "security_initialized": security_initialized,
                    "blocked_ips_count": blocked_ips_count,
                    "failed_attempts_count": failed_attempts_count
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="security_systems",
                status=HealthStatus.CRITICAL,
                message=f"Security systems check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_user_management(self) -> HealthCheck:
        """Check user management system"""
        start_time = time.time()
        
        try:
            # Test user repository operations
            active_users = await self.user_repository.get_active_users_count()
            
            # Test user search
            search_results = await self.user_repository.search_users("test", limit=1)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            status = HealthStatus.HEALTHY
            message = "User management system operational"
            
            return HealthCheck(
                name="user_management",
                status=status,
                message=message,
                details={
                    "response_time_ms": duration_ms,
                    "active_users_count": active_users,
                    "search_test": "passed" if isinstance(search_results, list) else "failed"
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="user_management",
                status=HealthStatus.CRITICAL,
                message=f"User management check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_token_cleanup(self) -> HealthCheck:
        """Check token cleanup system"""
        start_time = time.time()
        
        try:
            # Check token cleanup
            cleaned_count = await self.token_manager.cleanup_expired_tokens()
            
            # Check token monitoring
            monitoring_stats = await self.token_manager.monitor_expiration()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            status = HealthStatus.HEALTHY
            message = "Token cleanup system operational"
            
            return HealthCheck(
                name="token_cleanup",
                status=status,
                message=message,
                details={
                    "response_time_ms": duration_ms,
                    "tokens_cleaned": cleaned_count,
                    "monitoring_stats": monitoring_stats
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="token_cleanup",
                status=HealthStatus.CRITICAL,
                message=f"Token cleanup check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_system_resources(self) -> HealthCheck:
        """Check system resource usage"""
        start_time = time.time()
        
        try:
            import psutil
            
            # Check memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            status = HealthStatus.HEALTHY
            if memory_percent > self.thresholds["memory_usage_percent"] or cpu_percent > self.thresholds["cpu_usage_percent"]:
                status = HealthStatus.WARNING
                message = "High resource usage detected"
            else:
                message = "System resources normal"
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                details={
                    "response_time_ms": duration_ms,
                    "memory_usage_percent": memory_percent,
                    "cpu_usage_percent": cpu_percent,
                    "disk_usage_percent": disk_percent
                }
            )
            
        except ImportError:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message="psutil not available for resource monitoring",
                details={"error": "psutil package not installed"}
            )
        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.CRITICAL,
                message=f"System resource check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def _calculate_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Calculate overall health status from individual checks"""
        if not checks:
            return HealthStatus.UNKNOWN
        
        # Count statuses
        status_counts = {}
        for check in checks:
            status_counts[check.status] = status_counts.get(check.status, 0) + 1
        
        # Determine overall status
        if status_counts.get(HealthStatus.CRITICAL, 0) > 0:
            return HealthStatus.CRITICAL
        elif status_counts.get(HealthStatus.WARNING, 0) > 0:
            return HealthStatus.WARNING
        elif status_counts.get(HealthStatus.HEALTHY, 0) > 0:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def _generate_health_summary(self, checks: List[HealthCheck]) -> Dict[str, Any]:
        """Generate health summary"""
        total_checks = len(checks)
        healthy_checks = sum(1 for check in checks if check.status == HealthStatus.HEALTHY)
        warning_checks = sum(1 for check in checks if check.status == HealthStatus.WARNING)
        critical_checks = sum(1 for check in checks if check.status == HealthStatus.CRITICAL)
        
        return {
            "total_checks": total_checks,
            "healthy": healthy_checks,
            "warnings": warning_checks,
            "critical": critical_checks,
            "health_percentage": (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        }
    
    def _store_health_result(self, health_result: Dict[str, Any]):
        """Store health check result in history"""
        self.health_history.append(health_result)
        
        # Limit history size
        if len(self.health_history) > self.max_history_size:
            self.health_history = self.health_history[-self.max_history_size:]
    
    async def _check_and_send_alerts(self, health_result: Dict[str, Any]):
        """Check if alerts need to be sent"""
        try:
            current_time = time.time()
            status = health_result["status"]
            
            # Check if we should send an alert
            if status in ["warning", "critical"]:
                alert_key = f"alert:{status}"
                last_alert_time = self.last_alerts.get(alert_key, 0)
                
                if current_time - last_alert_time > self.alert_cooldown:
                    await self._send_alert(health_result)
                    self.last_alerts[alert_key] = current_time
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    async def _send_alert(self, health_result: Dict[str, Any]):
        """Send health alert"""
        try:
            # This would integrate with your alerting system (email, Slack, etc.)
            logger.warning(f"HEALTH ALERT: {health_result['status'].upper()} - {health_result['summary']}")
            
            # Example: Send to monitoring service
            # await self._send_to_monitoring_service(health_result)
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    async def get_health_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get health check history"""
        return self.health_history[-limit:] if self.health_history else []
    
    async def get_health_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get health metrics for specified time period"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter health history by time
            recent_history = [
                result for result in self.health_history
                if datetime.fromisoformat(result["timestamp"]) > cutoff_time
            ]
            
            if not recent_history:
                return {"error": "No health data available for the specified period"}
            
            # Calculate metrics
            total_checks = len(recent_history)
            healthy_checks = sum(1 for result in recent_history if result["status"] == "healthy")
            warning_checks = sum(1 for result in recent_history if result["status"] == "warning")
            critical_checks = sum(1 for result in recent_history if result["status"] == "critical")
            
            # Calculate average response time
            avg_response_time = sum(result["duration_ms"] for result in recent_history) / total_checks
            
            return {
                "period_hours": hours,
                "total_checks": total_checks,
                "healthy_checks": healthy_checks,
                "warning_checks": warning_checks,
                "critical_checks": critical_checks,
                "health_percentage": (healthy_checks / total_checks * 100) if total_checks > 0 else 0,
                "average_response_time_ms": avg_response_time,
                "uptime_percentage": (healthy_checks / total_checks * 100) if total_checks > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting health metrics: {e}")
            return {"error": str(e)}
