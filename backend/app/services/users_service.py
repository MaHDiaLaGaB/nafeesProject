from functools import lru_cache
from typing import List
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from crud.base_crud import BaseCRUD
from dependencies import DBSessionDep
from models.users import User as UserModel, UserRole
from schemas.users import UserOut, UserUpdate, UserBase


class UserService:
    def __init__(self, user_crud: BaseCRUD[UserModel]):
        self.user_crud = user_crud

    async def create_user(self, user_data: UserBase) -> UserOut:
        """Create a new user with given role and data."""
        try:
            user = await self.user_crud.create(user_data.model_dump(exclude_unset=True))
            if not user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create user")
            return user
        except SQLAlchemyError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during user creation")

    async def get_user_by_id(self, user_id: UUID) -> UserOut:
        """Retrieve a user by their ID."""
        user = await self.user_crud.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
        return user

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserOut]:
        """List users with pagination."""
        users = await self.user_crud.get_all(skip=skip, limit=limit)
        return [u for u in users]

    async def update_user(self, user_id: UUID, user_data: UserUpdate, current_user: UserOut) -> UserOut:
        """Update user data; only superadmin or owner can modify."""
        # fetch existing
        existing = await self.user_crud.get_by_id(user_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        # restrict superadmin edits
        if existing.role == UserRole.superadmin and current_user.role != UserRole.superadmin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify superadmin")

        try:
            updated = await self.user_crud.update(user_id, user_data.model_dump(exclude_unset=True))
            return updated
        except SQLAlchemyError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user")

    async def delete_user(self, user_id: UUID, current_user: UserOut) -> None:
        """Delete a user; only superadmin or owner can delete."""
        existing = await self.user_crud.get_by_id(user_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if existing.role == UserRole.superadmin and current_user.role != UserRole.superadmin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete superadmin")
        try:
            await self.user_crud.delete(user_id)
        except SQLAlchemyError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user")

    async def get_user_by_email(self, email: str) -> UserOut:
        """Retrieve a user by email address."""
        user = await self.user_crud.get_by_field("email", email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Email {email} not found")
        return user


@lru_cache()
def get_user_service(db: DBSessionDep) -> UserService:
    """Dependency provider for UserService."""
    return UserService(BaseCRUD(UserModel, db))
