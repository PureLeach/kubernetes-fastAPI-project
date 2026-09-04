"""Configuring application logging."""

from __future__ import annotations

import logging
import logging.config

import structlog


def build_log_config(level: str) -> dict[str, object]:
    """Return a `logging.config.dictConfig` document for the given root level."""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'text': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.dev.ConsoleRenderer(),
            },
            'json': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.processors.JSONRenderer(ensure_ascii=False),
                'foreign_pre_chain': [
                    structlog.contextvars.merge_contextvars,
                    structlog.processors.TimeStamper(fmt='iso'),
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                ],
            },
        },
        'handlers': {
            'console_text': {
                'class': 'logging.StreamHandler',
                'formatter': 'text',
            },
            'console_json': {
                'class': 'logging.StreamHandler',
                'formatter': 'json',
            },
        },
        'loggers': {
            'root': {
                'handlers': ['console_json'],
                'level': level.upper(),
                'propagate': False,
            },
        },
    }


def setup_logging(level: str = 'INFO') -> None:
    """
    Install the structlog/stdlib logging pipeline.

    The level is passed in rather than read from the settings singleton, so an
    app built with injected `Settings` logs at its own level.
    """
    logging.config.dictConfig(build_log_config(level))
    structlog.configure(
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
    )
