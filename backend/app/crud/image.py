import os
import datetime as dt
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.crud.base_crud import BaseCRUD
from app.models.images import UploadedImage
from app.logger import get_logger


class ImageCRUD(BaseCRUD[UploadedImage]):
    """
    CRUD helper dedicated to `UploadedImage`.

    Adds:
    • get_by_user()               – list images that belong to a user (with pagination)
    • get_recent()                – images uploaded in the last *n* days
    • delete() (override)         – removes both DB row *and* file on disk
    """

    def __init__(self, db_session: Session):
        super().__init__(UploadedImage, db_session)
        self.logger = get_logger()

    # ------------------------------------------------------------- #
    #                        Custom getters                         #
    # ------------------------------------------------------------- #

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UploadedImage]:
        """Return a page of images owned by a single user."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"user_id": user_id},
        )

    async def get_recent(
        self,
        days: int = 7,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UploadedImage]:
        """Images created in the last *days* (defaults to one week)."""
        since = dt.datetime.utcnow() - dt.timedelta(days=days)
        try:
            return (
                self.db_session.query(self.model)
                .filter(self.model.created_at >= since)
                .order_by(self.model.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            self.logger.error(
                "SQLAlchemyError in get_recent: %s",
                e,
                extra={"table": self.model.__tablename__, "days": days},
            )
            return []

    # ------------------------------------------------------------- #
    #                 Override delete() to clean disk               #
    # ------------------------------------------------------------- #

    async def delete(self, obj_id: UUID) -> None:  # type: ignore[override]
        """
        Remove the DB record **and** unlink the file_path, if present.

        Falls back to the parent implementation if anything goes wrong with
        the filesystem – we don't want a file-system error to leave the DB
        row orphaned.
        """
        try:
            obj: Optional[UploadedImage] = await self.get_by_id(obj_id)
            if not obj:
                return

            file_path = obj.file_path
            super_result = await super().delete(obj_id)  # call BaseCRUD.delete

            # If the DB delete succeeded, remove file from disk
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as fs_err:
                    # Log but don't raise – the DB state is already consistent
                    self.logger.warning(
                        "Could not delete file %s: %s",
                        file_path,
                        fs_err,
                        extra={
                            "table": self.model.__tablename__,
                            "id": str(obj_id),
                        },
                    )
            return super_result
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(
                "SQLAlchemyError in ImageCRUD.delete: %s",
                e,
                extra={"table": self.model.__tablename__, "id": str(obj_id)},
            )
