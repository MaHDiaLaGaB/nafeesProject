import os, uuid, pathlib, shutil, datetime as dt
from typing import Dict, Any
from uuid import UUID

from fastapi import HTTPException, UploadFile, Depends
from sqlalchemy.exc import SQLAlchemyError

from crud.image import ImageCRUD
from crud.base_crud import BaseCRUD
from models.images import UploadedImage
from models.users import User
from services.scan_service import ScanResultService, get_scan_service
from dependencies import DBSessionDep
from core.config import settings  # assume you have MEDIA_DIR in settings


class ImageService:
    def __init__(
        self,
        image_crud: ImageCRUD,
        user_crud: BaseCRUD[User],
        scan_svc: ScanResultService,
    ):
        self.image_crud = image_crud
        self.user_crud = user_crud
        self.scan_svc = scan_svc

    # --------------- upload & save ---------------- #
    async def store_image(
        self,
        user_id: UUID,
        file: UploadFile,
    ) -> UploadedImage:
        # 1) ensure user exists
        if not await self.user_crud.get_by_id(user_id):
            raise HTTPException(status_code=404, detail="User not found")

        # 2) create final path
        stamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        ext = pathlib.Path(file.filename).suffix or ".bin"
        fname = f"{uuid.uuid4()}_{stamp}{ext}"
        dir_ = pathlib.Path(settings.MEDIA_DIR) / "uploads"
        dir_.mkdir(parents=True, exist_ok=True)
        full_path = dir_ / fname

        # 3) write to disk
        try:
            with full_path.open("wb") as out:
                shutil.copyfileobj(file.file, out)
        finally:
            await file.close()

        # 4) write DB record
        record_in: Dict[str, Any] = dict(
            user_id=user_id,
            file_name=file.filename,
            file_path=str(full_path),
            mime_type=file.content_type,
            size=full_path.stat().st_size,
        )
        try:
            return await self.image_crud.create(record_in)
        except SQLAlchemyError:
            full_path.unlink(missing_ok=True)  # cleanup
            raise HTTPException(status_code=500, detail="Could not save upload")

    # --------------- combined upload + scan --------------- #
    async def upload_and_scan(
        self,
        user_id: UUID,
        file: UploadFile,
    ):
        img_record = await self.store_image(user_id, file)
        scan_record = await self.scan_svc.create_scan_result(
            {"user_id": user_id, "image_path": img_record.file_path}
        )
        return {"image": img_record, "scan": scan_record}


async def get_image_service(
    session: DBSessionDep,
    scan_svc: ScanResultService = Depends(get_scan_service),
) -> ImageService:
    """
    FastAPI dependency that constructs an ImageService
    with all its CRUD and scan-svc dependencies.
    """
    image_crud = ImageCRUD(session)
    user_crud = BaseCRUD(User, session)
    return ImageService(
        image_crud=image_crud,
        user_crud=user_crud,
        scan_svc=scan_svc,
    )
