import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from colorama import init, Fore, Style
from utils.utils import started_from_exe

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to console output based on log level."""
    # Define color formats for different log levels
    LEVEL_COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def __init__(self, fmt):
        super().__init__(fmt)

    def format(self, record):
        # Get the original format string
        format_str = self._fmt
        # Apply the color based on the log level
        color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)  # Default to white if level not found
        # Wrap the entire log message with the color
        formatted = color + super().format(record) + Style.RESET_ALL
        return formatted

def setup_logging(name, filename):
    log_dir = "logs"
    if started_from_exe():
        parent_log_dir = os.path.join(os.path.dirname(sys.executable), "logs")
    else:
        parent_log_dir = os.path.join(Path(__file__).parent.parent.parent, "logs")
    if not os.path.exists(parent_log_dir):
        os.makedirs(parent_log_dir)
    
    log_format = format='%(asctime)s - %(levelname)s - MODULE: %(module)s LINE:%(lineno)d - %(message)s'
    formatter = logging.Formatter(log_format)

    # Set up file handler
    log_file = os.path.join(parent_log_dir, filename)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024*1024,
        backupCount=1,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    console_formatter = ColoredFormatter(log_format)    
    #setup console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    # config root logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger 