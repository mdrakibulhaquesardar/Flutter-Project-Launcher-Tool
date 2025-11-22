"""Logging utilities for Flutter Project Launcher Tool."""
import logging
from datetime import datetime
from pathlib import Path


class Logger:
    """Singleton logger with file and console handlers."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        log_dir = Path.home() / ".flutter_launcher" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Get log level from settings (avoid circular dependency by checking if settings exist)
        log_level = logging.INFO  # Default
        try:
            # Try to get log level from database directly to avoid circular dependency
            from core.database import Database
            db = Database()
            log_level_str = db.get_setting("log_level")
            if log_level_str:
                log_level_map = {
                    "DEBUG": logging.DEBUG,
                    "INFO": logging.INFO,
                    "WARNING": logging.WARNING,
                    "ERROR": logging.ERROR
                }
                log_level = log_level_map.get(log_level_str, logging.INFO)
        except Exception:
            # If settings not available yet, use default
            pass
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("FlutterLauncher")
        self._initialized = True
    
    def set_log_level(self, level: str):
        """Set log level dynamically."""
        log_level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR
        }
        if level in log_level_map:
            self.logger.setLevel(log_level_map[level])
            for handler in self.logger.handlers:
                handler.setLevel(log_level_map[level])
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)


