# Enhanced logging configuration with comprehensive features

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
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
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'error_details'):
            log_entry['error_details'] = record.error_details
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_comprehensive_logging():
    """Enhanced logging setup with comprehensive features"""
    
    # Get configuration from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    environment = os.getenv("ENVIRONMENT", "development").lower()
    enable_json_logging = os.getenv("ENABLE_JSON_LOGGING", "false").lower() == "true"
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Console Handler with colored output for development
    console_handler = logging.StreamHandler(sys.stdout)
    if environment == "development" and not enable_json_logging:
        console_formatter = ColoredConsoleFormatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_formatter = StructuredFormatter()
    
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # File Handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    
    # Error File Handler
    error_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "error.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setFormatter(file_formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # API Access Log Handler
    api_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "api_access.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    api_handler.setFormatter(file_formatter)
    api_handler.setLevel(logging.INFO)
    
    # Create API logger
    api_logger = logging.getLogger("api_access")
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)
    api_logger.propagate = False
    
    # Database operations logger
    db_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "database.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    db_handler.setFormatter(file_formatter)
    db_logger = logging.getLogger("database")
    db_logger.addHandler(db_handler)
    db_logger.setLevel(logging.DEBUG)
    db_logger.propagate = False
    
    # Security events logger
    security_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "security.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=10
    )
    security_handler.setFormatter(file_formatter)
    security_logger = logging.getLogger("security")
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False
    
    print(f"[OK] Comprehensive logging initialized - Level: {log_level}, Environment: {environment}")
    print(f"[OK] Log files location: {LOGS_DIR.absolute()}")

def get_logger(name: str) -> logging.Logger:
    """Get logger instance with enhanced features"""
    return logging.getLogger(name)

def log_api_request(logger: logging.Logger, method: str, endpoint: str, 
                   user_id: Optional[str] = None, request_id: Optional[str] = None,
                   **kwargs):
    """Log API request with structured data"""
    extra = {
        'method': method,
        'endpoint': endpoint,
        'user_id': user_id,
        'request_id': request_id,
        **kwargs
    }
    logger.info(f"API Request: {method} {endpoint}", extra=extra)

def log_api_response(logger: logging.Logger, method: str, endpoint: str,
                    status_code: int, duration: float,
                    user_id: Optional[str] = None, request_id: Optional[str] = None,
                    **kwargs):
    """Log API response with structured data"""
    extra = {
        'method': method,
        'endpoint': endpoint,
        'status_code': status_code,
        'duration': duration,
        'user_id': user_id,
        'request_id': request_id,
        **kwargs
    }
    logger.info(f"API Response: {method} {endpoint} - {status_code} ({duration:.3f}s)", extra=extra)

def log_database_operation(operation: str, table: str, duration: float = None, 
                          record_count: int = None, **kwargs):
    """Log database operations"""
    db_logger = logging.getLogger("database")
    extra = {
        'operation': operation,
        'table': table,
        'duration': duration,
        'record_count': record_count,
        **kwargs
    }
    message = f"DB {operation}: {table}"
    if duration:
        message += f" ({duration:.3f}s)"
    if record_count is not None:
        message += f" - {record_count} records"
    
    db_logger.info(message, extra=extra)

def log_security_event(event_type: str, user_id: Optional[str] = None, 
                      ip_address: Optional[str] = None, details: Optional[Dict] = None):
    """Log security events"""
    security_logger = logging.getLogger("security")
    extra = {
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': ip_address,
        'details': details or {}
    }
    security_logger.warning(f"Security Event: {event_type}", extra=extra)

# Initialize logging when module is imported
if __name__ != "__main__":
    setup_comprehensive_logging()  
# 3. No structured logging
# 4. Silent failures
# 5. No log level configuration per module
# 6. No async logging support
# 7. Poor error handling

# --- What was likely scattered across files ---

# In various service files, you probably had:
logger = logging.getLogger(__name__)

# In main.py or similar:
import logging
logging.basicConfig(level=logging.INFO)

# In facebook_service.py:
import logging
logger = logging.getLogger(__name__)
# logger.error(f"Facebook config error: {e}")

# In auth_service.py:
import logging  
logger = logging.getLogger(__name__)
# logger.info(f"Access token created for user: {email}")
 