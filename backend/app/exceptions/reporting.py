import logging
from typing import Any, Dict, Optional

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from core.config import Settings


def setup(config: Settings) -> None:
    if config.SENTRY_DSN:
        logging_integration = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors and above as events
        )
        sentry_sdk.init(
            dsn=config.SENTRY_DSN,
            traces_sample_rate=1.0,
            environment=config.ENV,
            integrations=[logging_integration],
        )
        sentry_sdk.set_context("component", {"name": config.PROJECT_NAME})


def report_exception(exc: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    try:
        if context:
            sentry_sdk.set_context("additional_context", context)
        sentry_sdk.capture_exception(exc)
    except Exception as exc_inner:
        logging.error("Could not report Exception to Sentry: %s", exc_inner)
        raise exc_inner
