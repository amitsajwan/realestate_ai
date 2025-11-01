"""
Logging Configuration
===================
Centralized logging setup for the application
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file naming
current_date = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = LOGS_DIR / f"app_{current_date}.log"

# Logging format
LOG_FORMAT = "%(asctime)s | %(levelname)-5s | %(name)s | %(funcName)-10s :%(lineno)-5d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with standard configuration
    
    Args:
        name: The name for the logger, typically __name__
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if no handlers are set
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(
            logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        )
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        )
        logger.addHandler(console_handler)
        
        # Don't propagate to root logger
        logger.propagate = False
        
        # Log startup message
        logger.info(f"Logger initialized for {name}")
        logger.info(f"Log file: {LOG_FILE}")
    
    return logger

# Initialize root logger
root_logger = get_logger("app")
root_logger.info("Comprehensive logging initialized - Level: INFO, Environment: development")
root_logger.info(f"Log files location: {LOGS_DIR}")