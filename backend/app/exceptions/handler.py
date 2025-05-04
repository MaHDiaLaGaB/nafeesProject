from http import HTTPStatus
from typing import Any, Dict, Optional

from fastapi.responses import JSONResponse

from core.config import Settings

from .exception import ReportCreationException, ReportNotFoundException
from .logger_base import CustomLogger
from .reporting import report_exception

config = Settings()
custom_logger = CustomLogger(config)
logger = custom_logger.get_logger()


def handle_exception(
    exception: Exception, context: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    logger.error("An error occurred", exc_info=exception)
    report_exception(exception, context)

    if isinstance(exception, ReportCreationException):
        status_code = HTTPStatus.BAD_REQUEST
        detail = exception.description
    elif isinstance(exception, ReportNotFoundException):
        status_code = HTTPStatus.NOT_FOUND
        detail = exception.description
    else:
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        detail = "Internal Server Error"

    response = {"detail": detail}

    return JSONResponse(
        status_code=status_code,
        content=response,
    )
