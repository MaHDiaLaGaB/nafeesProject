import base64
import os
import json
from io import BytesIO
from functools import lru_cache
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, Depends
from sqlalchemy.exc import SQLAlchemyError
from transformers import pipeline
from PIL import Image

from crud.base_crud import BaseCRUD
from dependencies import DBSessionDep
from models.scan import ScanResult as ScanResultModel
from models.users import User as UserModel
from core.config import settings
from logger import get_logger

logger = get_logger(__name__)

# --------------------------------------------------------------------------- #
#                         HUGGING FACE PIPELINE                              #
# --------------------------------------------------------------------------- #

@lru_cache()
def get_image_classifier():
    """
    Returns a cached Hugging Face image-classification pipeline.
    """
    if not settings.HF_MODEL or not settings.HF_API_TOKEN:
        raise ValueError("Both HF_MODEL and HF_API_TOKEN must be set in .env")
    logger.info("Loading HF pipeline for model: %s", settings.HF_MODEL)
    return pipeline(
        task="image-classification",
        model=settings.HF_MODEL,
        token=settings.HF_API_TOKEN.get_secret_value(),
    )

# --------------------------------------------------------------------------- #
#                             IMAGE DECODING                                 #
# --------------------------------------------------------------------------- #

def decode_image_bytes(
    file: Optional[UploadFile] = None,
    image_b64: Optional[str]    = None
) -> Image.Image:
    """
    Decode an uploaded file or base64-encoded string into a PIL Image (RGB).
    """
    img_bytes: bytes = b""
    if file:
        img_bytes = file.file.read()
    elif image_b64:
        try:
            _, b64data = image_b64.split(",", 1) if "," in image_b64 else ("", image_b64)
            img_bytes = base64.b64decode(b64data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image")
    else:
        raise HTTPException(status_code=400, detail="No image provided")

    try:
        return Image.open(BytesIO(img_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to decode image bytes")

# --------------------------------------------------------------------------- #
#                            SERVICE LAYER                                    #
# --------------------------------------------------------------------------- #

class ScanResultService:
    def __init__(
        self,
        scan_crud: BaseCRUD[ScanResultModel],
        user_crud: BaseCRUD[UserModel],
        classifier,
    ):
        self.scan_crud = scan_crud
        self.user_crud = user_crud
        self.classifier = classifier

    async def create_scan(
        self,
        user_id: UUID,
        file: Optional[UploadFile] = None,
        image_b64: Optional[str] = None,
        extra: Dict[str, Any] = {}
    ) -> ScanResultModel:
        # 1) Ensure user exists
        user = await self.user_crud.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 2) Decode image and run classification
        try:
            img = decode_image_bytes(file=file, image_b64=image_b64)
            logger.debug("Running classification for user_id=%s", user_id)
            results = self.classifier(img, top_k=1)
            if not results:
                raise HTTPException(status_code=500, detail="Empty inference response")
            top = results[0]
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Inference pipeline failed")
            raise HTTPException(status_code=502, detail=f"Inference failed: {e}")

        # 3) Save image to disk and generate URL
        filename = f"{uuid4()}.jpg"
        upload_dir = getattr(settings, "UPLOAD_DIR", "./uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        img.save(file_path)
        base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
        image_url = f"{base_url}/uploads/{filename}"

        # 4) Prepare prediction JSON
        prediction = json.dumps({
            "label": top.get("label"),
            "score": top.get("score"),
        })

        # 5) Persist to database
        payload = {"user_id": str(user_id), "image_url": image_url, "prediction": prediction}
        payload.update(extra)
        try:
            return await self.scan_crud.create(payload)
        except SQLAlchemyError:
            logger.exception("Failed to save scan result")
            raise HTTPException(status_code=500, detail="Failed to save scan result")

    # placeholder for other CRUD methods: get_scan, list_scans, delete_scan


def get_scan_service(
    db: DBSessionDep,
    classifier=Depends(get_image_classifier),
) -> ScanResultService:
    return ScanResultService(
        BaseCRUD(ScanResultModel, db),
        BaseCRUD(UserModel, db),
        classifier,
    )
