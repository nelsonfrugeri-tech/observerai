import logging
from typing import Any

import structlog
from structlog.types import Processor


class LogDriver:
    def __init__(self) -> None:
        """
        Configure the structlog with the best practices for production environment.
        - Uses JSON format for logs
        - Adds timestamp in ISO format
        - Adds caller information
        - Configures log level
        """
        shared_processors: list[Processor] = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]

        structlog.configure(
            processors=[
                *shared_processors,
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.PrintLoggerFactory(),
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            cache_logger_on_first_use=True,
        )

    def get_logger(self) -> structlog.BoundLogger:
        """
        Returns a configured structlog logger.
        Usage:
            logger = get_logger(metric)
            logger.info("message", extra_field="value")
        """
        return structlog.get_logger()
