import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

import sentry_sdk
from colorlog import ColoredFormatter
from sentry_sdk.integrations.logging import LoggingIntegration

from core.config import Settings


class CustomLogger:
    def __init__(self, config: Settings, file_name: str = None):
        self.config = config
        self.file_name = file_name
        self.logger = logging.getLogger(self.config.PROJECT_NAME)

        self.setup_handlers()
        self.setup_sentry_integration()

    def setup_handlers(self):
        # Ensure logs directory exists
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        # Clear existing handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Set log level based on environment
        if self.config.ENV == "production":
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.DEBUG)

        # Console handler with color
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            "%(log_color)s%(levelname)-8s %(name)s:%(filename)s:%(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
        console_handler.setFormatter(console_formatter)

        # File handler with rotation
        file_handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, "app.log"),
            when="midnight",
            backupCount=7,
            encoding="utf-8",
            delay=False,
        )
        file_formatter = logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s:%(filename)s:%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def setup_sentry_integration(self):
        if self.config.SENTRY_DSN:
            sentry_logging = LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR,  # Send errors and above as events
            )
            sentry_sdk.init(
                dsn=self.config.SENTRY_DSN,
                environment=self.config.ENV,
                integrations=[sentry_logging],
            )

    def get_logger(self):
        return self.logger
