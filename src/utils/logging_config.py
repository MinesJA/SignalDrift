"""Centralized logging configuration for SignalDrift."""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import Config


def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """
    Set up centralized logging configuration.
    
    Args:
        name: Logger name (typically __name__ from the calling module).
              If None, returns the root logger.
    
    Returns:
        Configured logger instance.
    """
    # Get log level from config
    log_level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
    
    # Configure root logger only once
    if not logging.getLogger().handlers:
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(console_handler)
        
        # Optionally add file handler for production
        if not Config.DEBUG:
            log_dir = Path(__file__).parent.parent.parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_dir / 'signaldrift.log',
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    # Return named logger or root logger
    return logging.getLogger(name) if name else logging.getLogger()