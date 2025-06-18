from __future__ import annotations
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, File, UploadFile, status, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from dependencies import DBSessionDep
from services.image_service import get_image_service, ImageService
from services.scan_service import get_scan_service

# ---------- Pydantic I/O ---------- #
class ImageRead(BaseModel):
    id: UUID
    user_id: UUID
    file_name: str
    mime_type: str
    size: int
    created_at: str

    model_config = {"from_attributes": True}


class UploadAndScanResponse(BaseModel):
    image: ImageRead
    scan: dict  # you can wrap ScanResultRead here if you like


# ---------- Router ---------- #
router = APIRouter()


# ---------- Endpoints ---------- #
@router.post(
    "",
    response_model=ImageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image and store on disk",
)
async def upload_image(
    user_id: UUID,
    file: UploadFile = File(...),
    svc: ImageService = Depends(get_image_service),
):
    rec = await svc.store_image(user_id, file)
    return ImageRead.from_orm(rec)


@router.post(
    "/scan",
    response_model=UploadAndScanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload **and** run gemstone detection in a single request",
)
async def upload_and_scan(
    user_id: UUID,
    file: UploadFile = File(...),
    svc: ImageService = Depends(get_image_service),
):
    result = await svc.upload_and_scan(user_id, file)
    return UploadAndScanResponse(
        image=ImageRead.from_orm(result["image"]),
        scan=result["scan"],  # already a dict from service
    )


@router.get(
    "/{image_id}",
    summary="Download / preview the raw file",
    responses={404: {"description": "Image not found"}},
)
async def download_image(
    image_id: UUID,
    svc: ImageService = Depends(get_image_service),
):
    rec = await svc.image_crud.get_by_id(image_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(rec.file_path, media_type=rec.mime_type, filename=rec.file_name)
