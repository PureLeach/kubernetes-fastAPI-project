"""Configuring application logging."""

import logging
import logging.config

import structlog

from storage_service.settings.core import env

LOG_LEVEL_ROOT = env.str('LOG_LEVEL_ROOT', default='INFO')


LOG_CONFIG = {
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
            'level': LOG_LEVEL_ROOT,
            'propagate': False,
        },
    },
}


def setup_logging() -> None:
    logging.config.dictConfig(LOG_CONFIG)
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
