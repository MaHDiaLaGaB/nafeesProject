from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

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