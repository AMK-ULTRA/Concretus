import logging
import sys
from pathlib import Path

from Concretus.settings import LOG_FILE, LOG_FORMAT, LOG_LEVEL


class Logger:
    def __init__(self, name, log_file=LOG_FILE, level=LOG_LEVEL, log_format=LOG_FORMAT):
        """
        Initialize the Logger.

        Args:
            name (str): Name of the logger (usually the name of the module).
            log_file (str | Path): Path to the file where the logs will be saved.
            level (str | int): Minimum logging level (default from settings).
            log_format (str): Format of log messages (default from settings).
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # This condition checks if the variable log_file is an instance of the str class, meaning if it's a string
        # Convert log_file to a Path object if it's a string
        if isinstance(log_file, str):
            log_file = Path(log_file)

        # Ensure the log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Format of log messages
        formatter = logging.Formatter(log_format)

        # Handler for writing to a file
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Handler for writing to the console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def debug(self, message):
        """Logs a DEBUG level message."""
        self.logger.debug(message)

    def info(self, message):
        """Logs an INFO level message."""
        self.logger.info(message)

    def warning(self, message):
        """Logs a WARNING level message."""
        self.logger.warning(message)

    def error(self, message, exc_info=False):
        """Logs an ERROR level message.

        Args:
            message (str): Error message.
            exc_info (bool): If True, includes exception information (traceback).
        """
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message):
        """Logs a CRITICAL level message."""
        self.logger.critical(message)