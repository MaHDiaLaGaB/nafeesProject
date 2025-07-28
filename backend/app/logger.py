import inspect
from functools import lru_cache

from app.core.config import settings
from app.exceptions.logger_base import CustomLogger


def get_logger(file_name: str = None):
    if file_name is None:
        file_name = inspect.stack()[1].filename
    custom_logger = CustomLogger(settings, file_name)
    return custom_logger.get_logger()
