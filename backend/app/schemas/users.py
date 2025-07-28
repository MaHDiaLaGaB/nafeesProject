from uuid import UUID
import enum
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserRole(str, enum.Enum):
    merchant = "merchant"
    customer = "customer"
    superadmin = "superadmin"


class UserBase(BaseModel):
    email: EmailStr
    name: str | None = None
    role: UserRole = UserRole.customer
    is_active: bool = True
    is_verified: bool = False
    is_superadmin: bool = False
    is_merchant: bool = False
    is_customer: bool = True

    class Config:
        use_enum_values = True
        str_strip_whitespace = True
        str_min_length = 4
        str_max_length = 255
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat() if v else None,
        }


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=60)


class UserOut(UserBase):
    id: UUID
    created_at: datetime

    class ConfigDict:
        from_attributes = True
