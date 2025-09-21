"""
AI Logging Configuration
========================
Centralized logging configuration for AI operations
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger


class AIStructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for AI operations"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields for AI operations
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['service'] = 'realestate_ai'
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        # Add operation context
        if hasattr(record, 'operation'):
            log_record['operation'] = record.operation


def setup_ai_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup structured logging for AI operations"""
    
    # Create logger
    logger = logging.getLogger("ai_operations")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler()
    formatter = AIStructuredFormatter(
        '%(timestamp)s %(level)s %(service)s %(operation)s %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler for AI operations
    file_handler = logging.FileHandler('logs/ai_operations.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


class AILogger:
    """Centralized AI logging utility"""
    
    def __init__(self, logger_name: str = "ai_operations"):
        self.logger = logging.getLogger(logger_name)
    
    def log_operation_start(self, operation: str, context: Dict[str, Any], request_id: str = None):
        """Log the start of an AI operation"""
        self.logger.info(
            f"AI_OPERATION_START_{operation.upper()}",
            extra={
                "operation": operation,
                "request_id": request_id,
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_operation_success(self, operation: str, result: Dict[str, Any], request_id: str = None):
        """Log successful AI operation"""
        self.logger.info(
            f"AI_OPERATION_SUCCESS_{operation.upper()}",
            extra={
                "operation": operation,
                "request_id": request_id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_operation_error(self, operation: str, error: Exception, context: Dict[str, Any], request_id: str = None):
        """Log AI operation error"""
        self.logger.error(
            f"AI_OPERATION_ERROR_{operation.upper()}",
            extra={
                "operation": operation,
                "request_id": request_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_performance_metrics(self, operation: str, metrics: Dict[str, Any], request_id: str = None):
        """Log performance metrics for AI operations"""
        self.logger.info(
            f"AI_PERFORMANCE_METRICS_{operation.upper()}",
            extra={
                "operation": operation,
                "request_id": request_id,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_content_validation(self, operation: str, validation_results: Dict[str, Any], request_id: str = None):
        """Log content validation results"""
        self.logger.info(
            f"AI_CONTENT_VALIDATION_{operation.upper()}",
            extra={
                "operation": operation,
                "request_id": request_id,
                "validation_results": validation_results,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_api_call(self, operation: str, api_details: Dict[str, Any], request_id: str = None):
        """Log API call details"""
        self.logger.debug(
            f"AI_API_CALL_{operation.upper()}",
            extra={
                "operation": operation,
                "request_id": request_id,
                "api_details": api_details,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Global AI logger instance
ai_logger = AILogger()


def get_ai_logger() -> AILogger:
    """Get the global AI logger instance"""
    return ai_logger


# Logging configuration for different AI operations
AI_OPERATION_LEVELS = {
    "content_generation": "INFO",
    "branding_generation": "INFO", 
    "content_validation": "DEBUG",
    "api_calls": "DEBUG",
    "performance_metrics": "INFO",
    "error_handling": "ERROR"
}


def configure_ai_logging():
    """Configure logging for all AI operations"""
    
    # Setup main AI logger
    setup_ai_logging("INFO")
    
    # Configure specific loggers
    for operation, level in AI_OPERATION_LEVELS.items():
        logger = logging.getLogger(f"ai_{operation}")
        logger.setLevel(getattr(logging, level))
        
        # Add handlers if not already present
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = AIStructuredFormatter()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    
    return True
