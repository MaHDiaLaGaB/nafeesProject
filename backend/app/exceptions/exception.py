from http import HTTPStatus
from typing import Any, Dict, Optional, Type, Union

import sentry_sdk

from .const import ExceptionCategory

KNOWN_EXCEPTIONS: Dict[str, Type["AppException"]] = (
    {}
)  # pylint: disable=global-variable-not-assigned


def register_exception(
    exception_type: Type["AppException"],
) -> Type["AppException"]:
    key = exception_type.error_code()
    global KNOWN_EXCEPTIONS  # pylint: disable=global-variable-not-assigned
    if key in KNOWN_EXCEPTIONS:
        raise Exception(  # pylint: disable=broad-exception-raised
            f"Duplicate Exception with code {key} registered. "
            f"{KNOWN_EXCEPTIONS[key]} and {exception_type}"
        )
    if exception_type.category_code not in [item.value for item in ExceptionCategory]:
        raise Exception(  # pylint: disable=broad-exception-raised
            f"Unknown Category {exception_type.category_code}"
        )
    KNOWN_EXCEPTIONS[key] = exception_type
    return exception_type


class AppExceptionMeta(type):
    def __init__(cls, name, bases, dct):
        if bases:
            register_exception(cls)
        super().__init__(name, bases, dct)


class AppException(Exception, metaclass=AppExceptionMeta):
    category_code: int = ExceptionCategory.GENERIC
    exception_code: int = 1
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    description: Optional[str] = "Internal Server Error"
    payload: Optional[Dict[str, Any]] = None

    def __init__(
        self,
        description: Union[str, Any] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__()
        self.description = description or self.description
        self.payload = payload
        # Add exception details to Sentry
        sentry_sdk.set_extra("exception_payload", self.payload)
        sentry_sdk.set_tag("exception_category", self.category_code)
        sentry_sdk.set_tag("exception_code", self.exception_code)

    @classmethod
    def error_code(cls) -> str:
        return f"E{cls.category_code:03}{cls.exception_code:03}"


class CompanyNotFoundException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.ENTITY
    exception_code: int = 2
    status_code: HTTPStatus = HTTPStatus.NOT_FOUND
    description: str = "Company not found."


class CompanyCreationException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.VALIDATION
    exception_code: int = 3
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Failed to create company due to invalid data."


class DetectionNotFoundException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.ENTITY
    exception_code: int = 4
    status_code: HTTPStatus = HTTPStatus.NOT_FOUND
    description: str = "Detection not found."


class DetectionCreationException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.VALIDATION
    exception_code: int = 5
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Failed to create detection due to invalid data."


class ReportNotFoundException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.ENTITY
    exception_code: int = 6
    status_code: HTTPStatus = HTTPStatus.NOT_FOUND
    description: str = "Report not found."


class ReportCreationException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.VALIDATION
    exception_code: int = 7
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Failed to create report due to invalid data."


class CoordinateNotFoundException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.ENTITY
    exception_code: int = 8
    status_code: HTTPStatus = HTTPStatus.NOT_FOUND
    description: str = "Coordinate not found."


class CoordinateCreationException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.VALIDATION
    exception_code: int = 9
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Failed to create coordinate due to invalid data."


class AdminCreationException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.USERS
    exception_code: int = 10
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Failed to create admin user."


class AdminUpdateException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.USERS
    exception_code: int = 11
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Failed to update admin user."


class AdminPasswordResetException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.USERS
    exception_code: int = 12
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Failed to reset admin password."


class CompanyDeleteException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.ENTITY
    exception_code: int = 13
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Failed to delete company and associated admins."


class AdminNotFoundException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.USERS
    exception_code: int = 14
    status_code: HTTPStatus = HTTPStatus.NOT_FOUND
    description: str = "Admin user not found."


class UserNotFoundException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.USERS
    exception_code: int = 15
    status_code: HTTPStatus = HTTPStatus.NOT_FOUND
    description: str = "User not found."


class UserCreationException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.VALIDATION
    exception_code: int = 16
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Failed to create user due to invalid data."


class UserUpdateException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.VALIDATION
    exception_code: int = 17
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Failed to update user due to invalid data or permissions."


class UserDeleteException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.USERS
    exception_code: int = 18
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = (
        "Failed to delete user due to invalid permissions or user does not exist."
    )


class UserEmailNotFoundException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.USERS
    exception_code: int = 19
    status_code: HTTPStatus = HTTPStatus.NOT_FOUND
    description: str = "User with the specified email not found."


class SuperAdminException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.USERS
    exception_code: int = 20
    status_code: HTTPStatus = HTTPStatus.NOT_FOUND
    description: str = "not allowed to create superadmin"


class ImageDeleteException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.STORAGE
    exception_code: int = 21
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Field to delete the image"


class ImageFetchException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.STORAGE
    exception_code: int = 22
    status_code: HTTPStatus = HTTPStatus.NOT_FOUND
    description: str = "Field to fetch the Images"


class WebSocketDisconnect(AppException):
    category_code: ExceptionCategory = ExceptionCategory.GENERIC
    exception_code: int = 23
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "WebSocket connection was unexpectedly closed"


class ImageEncodeException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.STORAGE
    exception_code: int = 24
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    description: str = "Failed to encode image to Base64"


class ImageListException(AppException):
    category_code: ExceptionCategory = ExceptionCategory.STORAGE
    exception_code: int = 25
    status_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
    description: str = "Failed to list or process images in storage"
