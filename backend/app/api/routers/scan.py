# app/api_v1/scan.py
from uuid import UUID
from fastapi import APIRouter, Depends, File, UploadFile, Form

from app.services.scan_service import get_scan_service, ScanResultService

router = APIRouter()

@router.post("/scanning")
async def create_scan_result(
    user_id: UUID,
    file: UploadFile = File(None),
    image_b64: str = Form(None),
    svc: ScanResultService = Depends(get_scan_service),
):
    """
    Upload via multipart or base64 → local HF pipeline inference → save result.
    """
    extra: dict = {}  # TODO: capture any additional Form(...) fields
    return await svc.create_scan(
        user_id=user_id,
        file=file,
        image_b64=image_b64,
        extra=extra,
    )

@router.get("/{scan_id}")
async def read_scan(
    scan_id: UUID,
    svc: ScanResultService = Depends(get_scan_service),
):
    return await svc.get_scan(scan_id)

@router.get("/user/{user_id}")
async def list_user_scans(
    user_id: UUID,
    svc: ScanResultService = Depends(get_scan_service),
):
    return await svc.list_scans(user_id)

@router.delete("/{scan_id}", status_code=204)
async def delete_scan(
    scan_id: UUID,
    svc: ScanResultService = Depends(get_scan_service),
):
    await svc.delete_scan(scan_id)
