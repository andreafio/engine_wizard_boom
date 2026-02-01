"""Structured logging configuration."""
import logging
import structlog
from app.core.config import settings


def mask_sensitive_data(_, __, event_dict):
    """Mask sensitive information in logs."""
    sensitive_fields = ["email", "phone", "api_key", "password", "token"]
    
    for key in event_dict.keys():
        if any(field in key.lower() for field in sensitive_fields):
            if isinstance(event_dict[key], str) and event_dict[key]:
                event_dict[key] = "***MASKED***"
    
    return event_dict


def configure_logging():
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            mask_sensitive_data,
            structlog.processors.JSONRenderer() if settings.is_production
            else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    """Get a structured logger instance."""
    return structlog.get_logger(name)
