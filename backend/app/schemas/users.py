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
    role: str

class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=60)

class UserOut(UserBase):
    id: UUID
    created_at: datetime

    class ConfigDict:
        from_attributes = True