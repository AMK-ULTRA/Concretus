import logging
import sys
from pathlib import Path

from Concretus.settings import LOG_FILE, LOG_FORMAT, LOG_LEVEL

class Logger:
    _initialized = False  # Class variable to control initialization

    def __init__(self, name=None, log_file=LOG_FILE, level=LOG_LEVEL, log_format=LOG_FORMAT):
        """
        Initialize the Logger.

        :param str name: Name of the logger (usually the name of the module).
        :param str | Path log_file: Path to the file where the logs will be saved.
        :param str | int level: Minimum logging level (default from settings).
        :param str log_format: Format of log messages (default from settings).
        """

        # Use module name if not specified
        self.name = name or __name__
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(level)

        # Configure handlers only once (using the root logger)
        if not Logger._initialized:
            self._setup_handlers(log_file, log_format)
            Logger._initialized = True

    def _setup_handlers(self, log_file, log_format):
        """Configure handlers at the root logger level."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Ensure minimum level

        # This condition checks if the variable log_file is an instance of the str class, meaning if it's a string
        if isinstance(log_file, str):
            log_file = Path(log_file) # Convert log_file to a Path object if it's a string

        # Ensure the log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Format of log messages
        formatter = logging.Formatter(log_format)

        # Handler for writing to a file (FileHandler) (overwrite at start)
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Handler for writing to the console (ConsoleHandler)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

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
        :param str message: Error message.
        :param bool exc_info: If True, includes exception information (traceback).
        """

        self.logger.error(message, exc_info=exc_info)

    def critical(self, message):
        """Logs a CRITICAL level message."""

        self.logger.critical(message)