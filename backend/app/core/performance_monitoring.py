"""
Performance Monitoring System
============================
Comprehensive performance monitoring with metrics collection,
alerting, and optimization recommendations.
"""

import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import psutil
import threading
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = "ms"


@dataclass
class Alert:
    """Performance alert data structure."""
    id: str
    metric_name: str
    threshold: float
    current_value: float
    severity: str
    message: str
    timestamp: datetime
    resolved: bool = False


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.
    """
    
    def __init__(self, max_metrics_history: int = 1000):
        self.max_metrics_history = max_metrics_history
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics_history))
        self.alerts: List[Alert] = []
        self.thresholds = self._initialize_thresholds()
        self.monitoring_active = False
        self.monitor_thread = None
        
        logger.info("Initialized PerformanceMonitor")
    
    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize performance thresholds."""
        return {
            "api_response_time": {
                "warning": 200,  # ms
                "critical": 500  # ms
            },
            "database_query_time": {
                "warning": 100,  # ms
                "critical": 300  # ms
            },
            "memory_usage": {
                "warning": 80,  # percentage
                "critical": 90  # percentage
            },
            "cpu_usage": {
                "warning": 70,  # percentage
                "critical": 85  # percentage
            },
            "error_rate": {
                "warning": 1,  # percentage
                "critical": 5  # percentage
            }
        }
    
    def start_monitoring(self):
        """Start continuous performance monitoring."""
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Started performance monitoring")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Stopped performance monitoring")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Check for alerts
                self._check_alerts()
                
                # Sleep for monitoring interval
                time.sleep(10)  # Monitor every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def _collect_system_metrics(self):
        """Collect system-level performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric("cpu_usage", cpu_percent, unit="percent")
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric("memory_usage", memory.percent, unit="percent")
            self.record_metric("memory_available", memory.available / (1024**3), unit="GB")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_metric("disk_usage", (disk.used / disk.total) * 100, unit="percent")
            self.record_metric("disk_available", disk.free / (1024**3), unit="GB")
            
            # Network I/O
            net_io = psutil.net_io_counters()
            self.record_metric("network_bytes_sent", net_io.bytes_sent / (1024**2), unit="MB")
            self.record_metric("network_bytes_recv", net_io.bytes_recv / (1024**2), unit="MB")
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def record_metric(self, name: str, value: float, unit: str = "ms", tags: Dict[str, str] = None):
        """Record a performance metric."""
        try:
            metric = PerformanceMetric(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                unit=unit
            )
            
            self.metrics_history[name].append(metric)
            
            # Check if this metric triggers an alert
            self._check_metric_threshold(name, value)
            
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")
    
    def _check_metric_threshold(self, metric_name: str, value: float):
        """Check if a metric exceeds thresholds."""
        if metric_name not in self.thresholds:
            return
        
        thresholds = self.thresholds[metric_name]
        
        # Check critical threshold
        if "critical" in thresholds and value >= thresholds["critical"]:
            self._create_alert(
                metric_name=metric_name,
                threshold=thresholds["critical"],
                current_value=value,
                severity="critical",
                message=f"{metric_name} exceeded critical threshold: {value} >= {thresholds['critical']}"
            )
        
        # Check warning threshold
        elif "warning" in thresholds and value >= thresholds["warning"]:
            self._create_alert(
                metric_name=metric_name,
                threshold=thresholds["warning"],
                current_value=value,
                severity="warning",
                message=f"{metric_name} exceeded warning threshold: {value} >= {thresholds['warning']}"
            )
    
    def _create_alert(self, metric_name: str, threshold: float, current_value: float, 
                     severity: str, message: str):
        """Create a performance alert."""
        alert_id = f"{metric_name}_{int(datetime.utcnow().timestamp())}"
        
        alert = Alert(
            id=alert_id,
            metric_name=metric_name,
            threshold=threshold,
            current_value=current_value,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow()
        )
        
        self.alerts.append(alert)
        
        # Log alert
        if severity == "critical":
            logger.critical(f"PERFORMANCE ALERT: {message}")
        else:
            logger.warning(f"PERFORMANCE WARNING: {message}")
    
    def _check_alerts(self):
        """Check for resolved alerts."""
        current_time = datetime.utcnow()
        
        for alert in self.alerts:
            if alert.resolved:
                continue
            
            # Check if alert is still valid (within last 5 minutes)
            if current_time - alert.timestamp > timedelta(minutes=5):
                # Get latest metric value
                latest_metrics = self.metrics_history.get(alert.metric_name, deque())
                if latest_metrics:
                    latest_value = latest_metrics[-1].value
                    
                    # Check if alert is resolved
                    if latest_value < alert.threshold:
                        alert.resolved = True
                        logger.info(f"Alert {alert.id} resolved: {alert.metric_name} = {latest_value}")
    
    @asynccontextmanager
    async def measure_api_call(self, endpoint: str, method: str = "GET"):
        """Context manager for measuring API call performance."""
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            self.record_metric(
                "api_response_time",
                duration,
                unit="ms",
                tags={"endpoint": endpoint, "method": method}
            )
    
    @asynccontextmanager
    async def measure_database_query(self, query_type: str, table: str = None):
        """Context manager for measuring database query performance."""
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            self.record_metric(
                "database_query_time",
                duration,
                unit="ms",
                tags={"query_type": query_type, "table": table or "unknown"}
            )
    
    def get_metric_history(self, metric_name: str, minutes: int = 60) -> List[PerformanceMetric]:
        """Get metric history for the last N minutes."""
        if metric_name not in self.metrics_history:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history[metric_name] if m.timestamp >= cutoff_time]
    
    def get_metric_statistics(self, metric_name: str, minutes: int = 60) -> Dict[str, float]:
        """Get statistics for a metric over the last N minutes."""
        history = self.get_metric_history(metric_name, minutes)
        
        if not history:
            return {}
        
        values = [m.value for m in history]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1] if values else 0
        }
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def get_alerts_by_severity(self, severity: str) -> List[Alert]:
        """Get alerts by severity level."""
        return [alert for alert in self.alerts if alert.severity == severity]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "monitoring_active": self.monitoring_active,
            "total_metrics": len(self.metrics_history),
            "active_alerts": len(self.get_active_alerts()),
            "critical_alerts": len(self.get_alerts_by_severity("critical")),
            "warning_alerts": len(self.get_alerts_by_severity("warning")),
            "metrics": {}
        }
        
        # Get statistics for key metrics
        key_metrics = ["api_response_time", "database_query_time", "memory_usage", "cpu_usage"]
        
        for metric_name in key_metrics:
            if metric_name in self.metrics_history:
                stats = self.get_metric_statistics(metric_name, minutes=60)
                summary["metrics"][metric_name] = stats
        
        return summary
    
    def get_optimization_recommendations(self) -> List[Dict[str, str]]:
        """Get performance optimization recommendations."""
        recommendations = []
        
        # Check API response times
        api_stats = self.get_metric_statistics("api_response_time", minutes=60)
        if api_stats and api_stats.get("avg", 0) > 200:
            recommendations.append({
                "category": "API Performance",
                "issue": f"Average API response time is {api_stats['avg']:.2f}ms",
                "recommendation": "Consider implementing caching, database query optimization, or async processing"
            })
        
        # Check database query times
        db_stats = self.get_metric_statistics("database_query_time", minutes=60)
        if db_stats and db_stats.get("avg", 0) > 100:
            recommendations.append({
                "category": "Database Performance",
                "issue": f"Average database query time is {db_stats['avg']:.2f}ms",
                "recommendation": "Add database indexes, optimize queries, or implement connection pooling"
            })
        
        # Check memory usage
        memory_stats = self.get_metric_statistics("memory_usage", minutes=60)
        if memory_stats and memory_stats.get("avg", 0) > 80:
            recommendations.append({
                "category": "Memory Usage",
                "issue": f"Average memory usage is {memory_stats['avg']:.2f}%",
                "recommendation": "Consider implementing memory optimization, garbage collection tuning, or scaling"
            })
        
        # Check CPU usage
        cpu_stats = self.get_metric_statistics("cpu_usage", minutes=60)
        if cpu_stats and cpu_stats.get("avg", 0) > 70:
            recommendations.append({
                "category": "CPU Usage",
                "issue": f"Average CPU usage is {cpu_stats['avg']:.2f}%",
                "recommendation": "Consider optimizing algorithms, implementing caching, or scaling horizontally"
            })
        
        return recommendations
    
    def set_threshold(self, metric_name: str, warning: float = None, critical: float = None):
        """Set or update thresholds for a metric."""
        if metric_name not in self.thresholds:
            self.thresholds[metric_name] = {}
        
        if warning is not None:
            self.thresholds[metric_name]["warning"] = warning
        
        if critical is not None:
            self.thresholds[metric_name]["critical"] = critical
        
        logger.info(f"Updated thresholds for {metric_name}: warning={warning}, critical={critical}")
    
    def clear_old_alerts(self, hours: int = 24):
        """Clear alerts older than specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        original_count = len(self.alerts)
        
        self.alerts = [alert for alert in self.alerts if alert.timestamp >= cutoff_time]
        
        cleared_count = original_count - len(self.alerts)
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} old alerts")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_api_call(endpoint: str, method: str = "GET"):
    """Decorator for monitoring API call performance."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with performance_monitor.measure_api_call(endpoint, method):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def monitor_database_query(query_type: str, table: str = None):
    """Decorator for monitoring database query performance."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with performance_monitor.measure_database_query(query_type, table):
                return await func(*args, **kwargs)
        return wrapper
    return decorator