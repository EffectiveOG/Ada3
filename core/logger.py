import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import sys

def setup_logging(name='Ada', log_level=logging.INFO):
    """
    Configure and set up logging for the assistant
    
    Args:
        name: Logger name
        log_level: Logging level (default: INFO)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    try:
        # Create logs directory in project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(project_root, 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        # Create log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(logs_dir, f'{name.lower()}_{timestamp}.log')

        # Create logger instance
        logger = logging.getLogger(name)
        logger.setLevel(log_level)

        # Create formatters and handlers
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)

        # File handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)

        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        # Initial log messages
        logger.info(f"Logging initialized - {name}")
        logger.info(f"Log file created at: {log_file}")

        return logger

    except Exception as e:
        # Fallback to basic logging if setup fails
        logging.basicConfig(
            level=log_level,
            format=format_str,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logging.error(f"Failed to initialize custom logging: {e}")
        return logging.getLogger(name)

# Optional: Add convenience functions for common logging patterns
def log_exception(logger, message, exc_info=True):
    """
    Log an exception with full traceback
    
    Args:
        logger: Logger instance
        message: Error message
        exc_info: Whether to include exception info
    """
    logger.exception(message) if exc_info else logger.error(message)

def log_startup(logger, module_name):
    """
    Log module startup with a consistent format
    
    Args:
        logger: Logger instance
        module_name: Name of the module starting up
    """
    logger.info(f"Starting {module_name}...")

def log_shutdown(logger, module_name):
    """
    Log module shutdown with a consistent format
    
    Args:
        logger: Logger instance
        module_name: Name of the module shutting down
    """
    logger.info(f"Shutting down {module_name}...")

# Export the main setup function and convenience functions
__all__ = ['setup_logging', 'log_exception', 'log_startup', 'log_shutdown']