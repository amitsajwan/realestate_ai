"""
Production-Ready Logging Configuration
=====================================
Centralized logging system for monitoring and debugging
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'error_code'):
            log_entry['error_code'] = record.error_code
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'path'):
            log_entry['path'] = record.path
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False)

class ProductionFilter(logging.Filter):
    """Filter for production logging"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # In production, only log INFO and above
        return record.levelno >= logging.INFO

class DevelopmentFilter(logging.Filter):
    """Filter for development logging"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # In development, log everything
        return True

def get_logging_config(environment: str = "development") -> Dict[str, Any]:
    """Get logging configuration based on environment"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": JSONFormatter,
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "filters": {
            "production": {
                "()": ProductionFilter,
            },
            "development": {
                "()": DevelopmentFilter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "default",
                "stream": sys.stdout,
                "filters": ["development"]
            },
            "console_prod": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "json",
                "stream": sys.stdout,
                "filters": ["production"]
            },
            "file_app": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(logs_dir / "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": str(logs_dir / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "file_access": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(logs_dir / "access.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "file_audit": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(logs_dir / "audit.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": "DEBUG",
                "handlers": ["console", "file_app"],
                "propagate": False
            },
            "app": {
                "level": "DEBUG",
                "handlers": ["console", "file_app"],
                "propagate": False
            },
            "app.api": {
                "level": "INFO",
                "handlers": ["console", "file_access"],
                "propagate": False
            },
            "app.services": {
                "level": "INFO",
                "handlers": ["console", "file_app"],
                "propagate": False
            },
            "app.core": {
                "level": "INFO",
                "handlers": ["console", "file_app"],
                "propagate": False
            },
            "app.audit": {
                "level": "INFO",
                "handlers": ["file_audit"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file_app"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["file_access"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "ERROR",
                "handlers": ["file_error"],
                "propagate": False
            },
            "motor": {
                "level": "WARNING",
                "handlers": ["console", "file_app"],
                "propagate": False
            },
            "pymongo": {
                "level": "WARNING",
                "handlers": ["console", "file_app"],
                "propagate": False
            }
        }
    }
    
    # Adjust configuration based on environment
    if environment == "production":
        # In production, use JSON logging and remove console debug
        config["handlers"]["console"]["filters"] = ["production"]
        config["handlers"]["console"]["formatter"] = "json"
        config["loggers"][""]["handlers"] = ["console_prod", "file_app"]
        config["loggers"]["app"]["handlers"] = ["console_prod", "file_app"]
        config["loggers"]["app.api"]["handlers"] = ["console_prod", "file_access"]
        config["loggers"]["app.services"]["handlers"] = ["console_prod", "file_app"]
        config["loggers"]["app.core"]["handlers"] = ["console_prod", "file_app"]
    
    return config

def setup_logging(environment: str = "development"):
    """Setup logging configuration"""
    config = get_logging_config(environment)
    logging.config.dictConfig(config)
    
    # Set up audit logger
    audit_logger = logging.getLogger("app.audit")
    audit_logger.info("Logging system initialized", extra={
        "environment": environment,
        "timestamp": datetime.utcnow().isoformat()
    })

class AuditLogger:
    """Audit logging for security and compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger("app.audit")
    
    def log_user_action(self, user_id: str, action: str, resource: str, details: Dict[str, Any] = None):
        """Log user actions for audit trail"""
        self.logger.info(f"User action: {action}", extra={
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def log_security_event(self, event_type: str, user_id: str = None, ip_address: str = None, details: Dict[str, Any] = None):
        """Log security events"""
        self.logger.warning(f"Security event: {event_type}", extra={
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def log_data_access(self, user_id: str, resource_type: str, resource_id: str, action: str):
        """Log data access for compliance"""
        self.logger.info(f"Data access: {action}", extra={
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        })

# Global audit logger instance
audit_logger = AuditLogger()

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(f"app.{name}")

def log_request(request_id: str, method: str, path: str, user_id: str = None, duration: float = None):
    """Log HTTP request"""
    logger = get_logger("api")
    logger.info(f"Request: {method} {path}", extra={
        "request_id": request_id,
        "method": method,
        "path": path,
        "user_id": user_id,
        "duration": duration,
        "timestamp": datetime.utcnow().isoformat()
    })

def log_error(error: Exception, request_id: str = None, user_id: str = None, context: Dict[str, Any] = None):
    """Log application errors"""
    logger = get_logger("core")
    logger.error(f"Application error: {str(error)}", extra={
        "request_id": request_id,
        "user_id": user_id,
        "context": context or {},
        "timestamp": datetime.utcnow().isoformat()
    }, exc_info=True)
