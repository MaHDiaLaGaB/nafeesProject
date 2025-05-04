from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from logger import get_logger

T = TypeVar("T", bound=BaseModel)


class Base:
    """Base class for SQLAlchemy models with common metadata."""

    id: UUID
    created_at: datetime
    updated_at: datetime


class BaseCRUD(Generic[T]):
    def __init__(self, model: Type[Base], db_session: Session):
        self.model = model
        self.db_session = db_session
        self.logger = get_logger()

    async def get_by_id(self, obj_id: UUID) -> Optional[T]:
        """Retrieve an object by its ID."""
        try:
            return (
                self.db_session.query(self.model)
                .filter(self.model.id == obj_id)
                .first()
            )
        except SQLAlchemyError as e:
            self.logger.error(
                "SQLAlchemyError in get_by_id: %s",
                e,
                extra={"table": self.model.__tablename__, "id": str(obj_id)},
            )
            return None

    async def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """Retrieve an object by a specific field."""
        if not hasattr(self.model, field_name):
            self.logger.error(
                "Invalid field: %s does not exist in table %s",
                field_name,
                self.model.__tablename__,
            )
            return None

        try:
            result = (
                self.db_session.query(self.model)
                .filter(getattr(self.model, field_name) == value)
                .first()
            )
            return result
        except SQLAlchemyError as e:
            self.logger.error(
                "SQLAlchemyError in get_by_field: %s",
                e,
                extra={
                    "table": self.model.__tablename__,
                    "field": field_name,
                    "value": value,
                },
            )
            return None

    async def get_all_by_field(self, field_name: str, value: Any) -> List[T]:
        """Retrieve all objects by a specific field."""
        if not hasattr(self.model, field_name):
            self.logger.error(
                "Invalid field: %s does not exist in table %s",
                field_name,
                self.model.__tablename__,
            )
            return []

        try:
            results = (
                self.db_session.query(self.model)
                .filter(getattr(self.model, field_name) == value)
                .all()  # Use `.all()` to retrieve all matching rows
            )
            return results
        except SQLAlchemyError as e:
            self.logger.error(
                "SQLAlchemyError in get_all_by_field: %s",
                e,
                extra={
                    "table": self.model.__tablename__,
                    "field": field_name,
                    "value": value,
                },
            )
            return []

    async def get_all(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Retrieve all objects with optional pagination and filtering."""
        try:
            query = self.db_session.query(self.model)
            if filters:
                for key, value in filters.items():
                    query = query.filter(getattr(self.model, key) == value)
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            self.logger.error(
                "SQLAlchemyError in get_all: %s",
                e,
                extra={
                    "table": self.model.__tablename__,
                    "skip": skip,
                    "limit": limit,
                    "filters": filters,
                },
            )
            return []

    async def create(self, data: Dict[str, Any]) -> Optional[T]:
        """Create a new object."""
        try:
            obj = self.model(**data)
            self.db_session.add(obj)
            self.db_session.commit()
            self.db_session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(
                "SQLAlchemyError in create: %s",
                e,
                extra={"table": self.model.__tablename__, "data": data},
            )
            return None

    async def update(self, obj_id: UUID, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing object."""
        try:
            # Exclude "id" from updates
            data = {key: value for key, value in data.items() if key != "id"}

            # Add `updated_at` to the data if the model supports it
            if hasattr(self.model, "updated_at"):
                data["updated_at"] = datetime.utcnow()

            # Perform the update using SQLAlchemy's update construct
            stmt = (
                update(self.model)
                .where(self.model.id == obj_id)
                .values(**data)
                .execution_options(
                    synchronize_session="fetch"
                )  # Ensures session consistency
            )

            result = self.db_session.execute(stmt)
            self.db_session.commit()

            # If no rows were updated, the object doesn't exist
            if result.rowcount == 0:
                return None

            # Fetch and return the updated object if needed
            updated_obj = (
                self.db_session.query(self.model)
                .filter(self.model.id == obj_id)
                .first()
            )
            return updated_obj

        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(
                "SQLAlchemyError in update: %s",
                e,
                extra={
                    "table": self.model.__tablename__,
                    "id": str(obj_id),
                    "data": data,
                },
            )
            return None

    async def delete(self, obj_id: UUID) -> None:
        """Delete an object."""
        try:
            obj = (
                self.db_session.query(self.model)
                .filter(self.model.id == obj_id)
                .first()
            )
            if obj:
                self.db_session.delete(obj)
                self.db_session.commit()
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(
                "SQLAlchemyError in delete: %s",
                e,
                extra={"table": self.model.__tablename__, "id": str(obj_id)},
            )
