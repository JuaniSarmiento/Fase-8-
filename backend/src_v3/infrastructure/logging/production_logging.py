"""Production Logging Configuration.

Provides structured logging with rotation, compression, and monitoring integration.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
import json


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for better parsing in production monitoring tools."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address
        
        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored formatter for development console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors."""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_production_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    enable_json: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 10,
):
    """Setup production-grade logging.
    
    Args:
        log_dir: Directory for log files
        log_level: Minimum log level
        enable_json: Enable JSON formatting for production
        max_bytes: Max size per log file
        backup_count: Number of backup files to keep
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler (always colored in development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    if enable_json:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_formatter = ColoredConsoleFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
    
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    all_log_file = log_path / "application.log"
    file_handler = logging.handlers.RotatingFileHandler(
        all_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8',
    )
    file_handler.setLevel(logging.DEBUG)
    
    if enable_json:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
    
    root_logger.addHandler(file_handler)
    
    # Error-only log file
    error_log_file = log_path / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8',
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        JSONFormatter() if enable_json else logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    )
    root_logger.addHandler(error_handler)
    
    # Security log file (for auth events)
    security_log_file = log_path / "security.log"
    security_handler = logging.handlers.RotatingFileHandler(
        security_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8',
    )
    security_handler.setLevel(logging.INFO)
    security_handler.addFilter(lambda record: 'security' in record.name.lower() or 'auth' in record.name.lower())
    security_handler.setFormatter(
        JSONFormatter() if enable_json else logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
    )
    root_logger.addHandler(security_handler)
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    
    logging.info(f"✅ Production logging initialized (Level: {log_level}, JSON: {enable_json})")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
