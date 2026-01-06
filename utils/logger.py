"""Logging utility module for ytdlp-online application.

This module provides centralized logging configuration with:
- Colored console output (always enabled)
- Optional file logging with rotation
- SSE stream monitoring utilities
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import uuid
from datetime import datetime
from contextlib import contextmanager


# Try to import colorlog for colored console output
try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


class SSEStreamLogger:
    """Utility class for tracking and logging SSE stream connections."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.active_streams = {}
    
    def start_stream(self, stream_id: Optional[str] = None) -> str:
        """Start tracking a new SSE stream.
        
        Args:
            stream_id: Optional stream ID, will generate UUID if not provided
            
        Returns:
            Stream ID
        """
        if stream_id is None:
            stream_id = str(uuid.uuid4())[:8]
        
        self.active_streams[stream_id] = {
            'start_time': datetime.now(),
            'events_sent': 0,
            'bytes_sent': 0
        }
        
        self.logger.info(f"SSE stream started: {stream_id}")
        return stream_id
    
    def log_event(self, stream_id: str, event_data: str):
        """Log an SSE event.
        
        Args:
            stream_id: Stream ID
            event_data: Event data content
        """
        if stream_id in self.active_streams:
            self.active_streams[stream_id]['events_sent'] += 1
            self.active_streams[stream_id]['bytes_sent'] += len(event_data.encode('utf-8'))
            self.logger.debug(f"SSE [{stream_id}] Event sent: {event_data[:100]}...")
    
    def end_stream(self, stream_id: str, normal: bool = True):
        """End tracking an SSE stream.
        
        Args:
            stream_id: Stream ID
            normal: Whether the stream ended normally
        """
        if stream_id in self.active_streams:
            stream_info = self.active_streams[stream_id]
            duration = (datetime.now() - stream_info['start_time']).total_seconds()
            
            status = "completed" if normal else "abnormally terminated"
            self.logger.info(
                f"SSE stream {status}: {stream_id} | "
                f"Duration: {duration:.2f}s | "
                f"Events: {stream_info['events_sent']} | "
                f"Bytes: {stream_info['bytes_sent']}"
            )
            
            del self.active_streams[stream_id]
    
    @contextmanager
    def stream_context(self, stream_id: Optional[str] = None):
        """Context manager for SSE stream logging.
        
        Args:
            stream_id: Optional stream ID
            
        Yields:
            Stream ID
        """
        sid = self.start_stream(stream_id)
        try:
            yield sid
            self.end_stream(sid, normal=True)
        except Exception as e:
            self.logger.error(f"SSE stream error [{sid}]: {e}", exc_info=True)
            self.end_stream(sid, normal=False)
            raise


def setup_logging(log_level: int, enable_file: bool = False, log_file: str = "logs/app.log"):
    """Setup application logging with console and optional file handlers.
    
    Args:
        log_level: Python logging level constant (e.g., logging.INFO)
        enable_file: Whether to enable file logging
        log_file: Path to log file (only used if enable_file is True)
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Console handler (always enabled)
    if HAS_COLORLOG:
        # Use colored output if colorlog is available
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt=date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        console_formatter = logging.Formatter(log_format, datefmt=date_format)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if enable_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        root_logger.info(f"File logging enabled: {log_file}")
    else:
        root_logger.info("File logging disabled (console only)")
    
    root_logger.info(f"Logging initialized at level: {logging.getLevelName(log_level)}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def get_sse_logger(logger: logging.Logger) -> SSEStreamLogger:
    """Get an SSE stream logger instance.
    
    Args:
        logger: Base logger instance
        
    Returns:
        SSE stream logger
    """
    return SSEStreamLogger(logger)
