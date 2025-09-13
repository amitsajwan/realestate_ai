"""
Application Monitoring
=====================
Comprehensive monitoring and metrics collection for the Real Estate Platform
"""

import time
import logging
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict, deque
import psutil
import os

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and stores application metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics = defaultdict(lambda: deque(maxlen=max_history))
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.timers = defaultdict(list)
        
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        key = f"{name}:{tags or ''}"
        self.counters[key] += value
        self.metrics['counters'].append({
            'name': name,
            'value': value,
            'tags': tags or {},
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        key = f"{name}:{tags or ''}"
        self.gauges[key] = value
        self.metrics['gauges'].append({
            'name': name,
            'value': value,
            'tags': tags or {},
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer metric"""
        key = f"{name}:{tags or ''}"
        self.timers[key].append(duration)
        self.metrics['timers'].append({
            'name': name,
            'duration': duration,
            'tags': tags or {},
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics"""
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'timers': {
                name: {
                    'count': len(times),
                    'min': min(times) if times else 0,
                    'max': max(times) if times else 0,
                    'avg': sum(times) / len(times) if times else 0,
                    'p95': sorted(times)[int(len(times) * 0.95)] if times else 0,
                    'p99': sorted(times)[int(len(times) * 0.99)] if times else 0
                }
                for name, times in self.timers.items()
            },
            'system': self.get_system_metrics()
        }
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            process = psutil.Process()
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'process_cpu_percent': process.cpu_percent(),
                'process_memory_mb': process.memory_info().rss / 1024 / 1024,
                'process_threads': process.num_threads(),
                'process_fds': process.num_fds() if hasattr(process, 'num_fds') else 0,
                'uptime_seconds': time.time() - process.create_time()
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}


# Global metrics collector
metrics = MetricsCollector()


def monitor_request(func):
    """Decorator to monitor request metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        status = "success"
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status = "error"
            metrics.increment_counter("request_errors", tags={"error_type": type(e).__name__})
            raise
        finally:
            duration = time.time() - start_time
            metrics.record_timer("request_duration", duration, tags={"status": status})
            metrics.increment_counter("requests_total", tags={"status": status})
            
    return wrapper


def monitor_database_operation(func):
    """Decorator to monitor database operations"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        operation = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            metrics.increment_counter("db_operations", tags={"operation": operation, "status": "success"})
            return result
        except Exception as e:
            metrics.increment_counter("db_operations", tags={"operation": operation, "status": "error"})
            metrics.increment_counter("db_errors", tags={"operation": operation, "error_type": type(e).__name__})
            raise
        finally:
            duration = time.time() - start_time
            metrics.record_timer("db_operation_duration", duration, tags={"operation": operation})
            
    return wrapper


class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self):
        self.checks = {}
        self.last_check = {}
        
    def register_check(self, name: str, check_func, timeout: float = 5.0):
        """Register a health check"""
        self.checks[name] = {
            'function': check_func,
            'timeout': timeout
        }
        
    async def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check"""
        if name not in self.checks:
            return {'status': 'error', 'message': f'Check {name} not found'}
            
        check = self.checks[name]
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                check['function'](),
                timeout=check['timeout']
            )
            
            duration = time.time() - start_time
            self.last_check[name] = {
                'status': 'healthy',
                'duration': duration,
                'timestamp': datetime.utcnow().isoformat(),
                'result': result
            }
            
            return self.last_check[name]
            
        except asyncio.TimeoutError:
            self.last_check[name] = {
                'status': 'timeout',
                'duration': check['timeout'],
                'timestamp': datetime.utcnow().isoformat(),
                'message': f'Check {name} timed out after {check["timeout"]}s'
            }
            return self.last_check[name]
            
        except Exception as e:
            duration = time.time() - start_time
            self.last_check[name] = {
                'status': 'error',
                'duration': duration,
                'timestamp': datetime.utcnow().isoformat(),
                'message': str(e)
            }
            return self.last_check[name]
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        
        for name in self.checks:
            results[name] = await self.run_check(name)
            
        return results
    
    def get_overall_status(self) -> str:
        """Get overall health status"""
        if not self.last_check:
            return 'unknown'
            
        statuses = [check['status'] for check in self.last_check.values()]
        
        if 'error' in statuses or 'timeout' in statuses:
            return 'unhealthy'
        elif 'healthy' in statuses:
            return 'healthy'
        else:
            return 'unknown'


# Global health checker
health_checker = HealthChecker()


async def check_database_health():
    """Check database connectivity"""
    try:
        from app.core.database import get_database
        db = get_database()
        
        # Simple ping to check connection
        await db.admin.command('ping')
        
        return {
            'message': 'Database connection healthy',
            'database': db.name
        }
    except Exception as e:
        raise Exception(f"Database health check failed: {str(e)}")


async def check_redis_health():
    """Check Redis connectivity (if available)"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        
        return {
            'message': 'Redis connection healthy',
            'version': r.info()['redis_version']
        }
    except ImportError:
        return {'message': 'Redis not available'}
    except Exception as e:
        raise Exception(f"Redis health check failed: {str(e)}")


async def check_disk_space():
    """Check available disk space"""
    try:
        disk_usage = psutil.disk_usage('/')
        free_percent = (disk_usage.free / disk_usage.total) * 100
        
        if free_percent < 10:
            raise Exception(f"Low disk space: {free_percent:.1f}% free")
            
        return {
            'message': 'Disk space healthy',
            'free_percent': round(free_percent, 1),
            'free_gb': round(disk_usage.free / (1024**3), 1)
        }
    except Exception as e:
        raise Exception(f"Disk space check failed: {str(e)}")


async def check_memory_usage():
    """Check memory usage"""
    try:
        memory = psutil.virtual_memory()
        
        if memory.percent > 90:
            raise Exception(f"High memory usage: {memory.percent}%")
            
        return {
            'message': 'Memory usage healthy',
            'usage_percent': memory.percent,
            'available_gb': round(memory.available / (1024**3), 1)
        }
    except Exception as e:
        raise Exception(f"Memory check failed: {str(e)}")


# Register health checks
health_checker.register_check('database', check_database_health)
health_checker.register_check('redis', check_redis_health)
health_checker.register_check('disk_space', check_disk_space)
health_checker.register_check('memory', check_memory_usage)


class PerformanceMonitor:
    """Performance monitoring and alerting"""
    
    def __init__(self):
        self.alert_thresholds = {
            'response_time': 2.0,  # seconds
            'error_rate': 0.05,    # 5%
            'cpu_usage': 80.0,     # percentage
            'memory_usage': 85.0,  # percentage
            'disk_usage': 90.0     # percentage
        }
        self.alerts = deque(maxlen=100)
        
    def check_performance(self, metrics_summary: Dict[str, Any]) -> list:
        """Check performance metrics against thresholds"""
        alerts = []
        
        # Check response times
        if 'timers' in metrics_summary:
            for timer_name, timer_data in metrics_summary['timers'].items():
                if 'request_duration' in timer_name and timer_data['avg'] > self.alert_thresholds['response_time']:
                    alerts.append({
                        'type': 'performance',
                        'metric': 'response_time',
                        'value': timer_data['avg'],
                        'threshold': self.alert_thresholds['response_time'],
                        'message': f'High response time: {timer_data["avg"]:.2f}s'
                    })
        
        # Check system metrics
        if 'system' in metrics_summary:
            system = metrics_summary['system']
            
            if system.get('cpu_percent', 0) > self.alert_thresholds['cpu_usage']:
                alerts.append({
                    'type': 'system',
                    'metric': 'cpu_usage',
                    'value': system['cpu_percent'],
                    'threshold': self.alert_thresholds['cpu_usage'],
                    'message': f'High CPU usage: {system["cpu_percent"]}%'
                })
                
            if system.get('memory_percent', 0) > self.alert_thresholds['memory_usage']:
                alerts.append({
                    'type': 'system',
                    'metric': 'memory_usage',
                    'value': system['memory_percent'],
                    'threshold': self.alert_thresholds['memory_usage'],
                    'message': f'High memory usage: {system["memory_percent"]}%'
                })
                
            if system.get('disk_percent', 0) > self.alert_thresholds['disk_usage']:
                alerts.append({
                    'type': 'system',
                    'metric': 'disk_usage',
                    'value': system['disk_percent'],
                    'threshold': self.alert_thresholds['disk_usage'],
                    'message': f'High disk usage: {system["disk_percent"]}%'
                })
        
        # Store alerts
        for alert in alerts:
            alert['timestamp'] = datetime.utcnow().isoformat()
            self.alerts.append(alert)
            
        return alerts
    
    def get_recent_alerts(self, hours: int = 24) -> list:
        """Get recent alerts"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert['timestamp']) > cutoff
        ]


# Global performance monitor
performance_monitor = PerformanceMonitor()


async def collect_metrics_periodically():
    """Periodically collect and process metrics"""
    while True:
        try:
            # Collect system metrics
            metrics_summary = metrics.get_metrics_summary()
            
            # Check for performance issues
            alerts = performance_monitor.check_performance(metrics_summary)
            
            if alerts:
                logger.warning(f"Performance alerts: {len(alerts)} issues detected")
                for alert in alerts:
                    logger.warning(f"Alert: {alert['message']}")
            
            # Log metrics summary (in production, this would go to a monitoring system)
            logger.info(f"Metrics collected: {len(metrics_summary.get('counters', {}))} counters, "
                       f"{len(metrics_summary.get('gauges', {}))} gauges, "
                       f"{len(metrics_summary.get('timers', {}))} timers")
            
            # Wait before next collection
            await asyncio.sleep(60)  # Collect every minute
            
        except Exception as e:
            logger.error(f"Error in metrics collection: {e}")
            await asyncio.sleep(60)


def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status"""
    return {
        'status': health_checker.get_overall_status(),
        'timestamp': datetime.utcnow().isoformat(),
        'checks': health_checker.last_check,
        'metrics': metrics.get_metrics_summary(),
        'alerts': performance_monitor.get_recent_alerts(hours=1)
    }