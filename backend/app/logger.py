import inspect
from functools import lru_cache

from core.config import settings
from exceptions.logger_base import CustomLogger


@lru_cache()
def get_logger(file_name: str = None):
    if file_name is None:
        file_name = inspect.stack()[1].filename
    custom_logger = CustomLogger(settings, file_name)
    return custom_logger.get_logger()
