# app/api_v1/scan.py
from uuid import uuid4
import os

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from dependencies.deps import CurrentUser, DBSessionDep
from dependencies.auth import role_required
from schemas.scan import ScanResultOut
from services.scan_service import get_scan_service, ScanResultService

router = APIRouter()


@router.post(
    "/scanning",
    summary="Upload an image, run scan prediction, and record the result",
)
async def upload_and_scan(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    scan_service: ScanResultService = Depends(get_scan_service),
):
    # 1) save upload locally (or to your storage of choice)
    upload_dir = "uploads/scans"
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid4().hex}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)

    try:
        contents = await file.read()
        with open(file_path, "wb") as out_file:
            out_file.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not save uploaded file")

    # 2) run your prediction logic (stubbed here)
    #    Replace `perform_scan_prediction` with your actual inference call
    try:
        pass
        # prediction = await perform_scan_prediction(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Scan prediction failed")

    # 3) record in DB
    try:
        scan = await scan_service.create_scan_result({
            "user_id": current_user.id,
            "image_url": file_path,
            # "prediction": prediction,
        })
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Failed to persist scan result")

    if not scan:
        raise HTTPException(status_code=500, detail="Unknown error")
    return scan
