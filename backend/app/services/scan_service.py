# app/services/scan_result_service.py
from __future__ import annotations

import base64
import io
from functools import lru_cache
from typing import List, Dict, Any
from uuid import UUID

import torch
from PIL import Image
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from transformers import AutoModelForImageClassification, AutoImageProcessor

from crud.base_crud import BaseCRUD
from dependencies import DBSessionDep
from models.scan import ScanResult as ScanResultModel
from models.users import User as UserModel

# --------------------------------------------------------------------------- #
# ---------------------  ML utilities: load + inference  -------------------- #
# --------------------------------------------------------------------------- #

MODEL_DIR = "gemstones_image_detection"  # same value you used in TrainingArguments


@lru_cache()
def _load_model_and_processor():
    """
    Loads the model and processor exactly once per process.
    """
    model = AutoModelForImageClassification.from_pretrained(MODEL_DIR)
    processor = AutoImageProcessor.from_pretrained(MODEL_DIR)
    model.eval()  # we only do inference here
    return model, processor


def _run_inference(img: Image.Image) -> Dict[str, Any]:
    """
    Returns {"predicted_label": str, "confidence": float}
    """
    model, processor = _load_model_and_processor()
    inputs = processor(images=img, return_tensors="pt").to(model.device)
    with torch.no_grad():
        logits = model(**inputs).logits.squeeze(0)  # shape: [num_labels]
    probs = logits.softmax(dim=0)
    conf, idx = torch.max(probs, dim=0)
    label = model.config.id2label[int(idx)]
    return {"predicted_label": label, "confidence": conf.item()}


def _decode_image(data: Dict[str, Any]) -> Image.Image:
    """
    Turn either an uploaded base64 string or an on-disk path into a PIL image.
    """
    if "image_b64" in data:  # TODO: adjust key to match your payload
        try:
            raw = base64.b64decode(data["image_b64"])
            return Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image")
    elif "image_path" in data:  # TODO: adjust key to match your payload
        try:
            return Image.open(data["image_path"]).convert("RGB")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Image file not found")
    else:
        raise HTTPException(
            status_code=400,
            detail="Request body must include either 'image_b64' or 'image_path'",
        )


# --------------------------------------------------------------------------- #
# ---------------------------  Main service class  -------------------------- #
# --------------------------------------------------------------------------- #


class ScanResultService:
    def __init__(
        self,
        scan_crud: BaseCRUD[ScanResultModel],
        user_crud: BaseCRUD[UserModel],
    ):
        self.scan_crud = scan_crud
        self.user_crud = user_crud

    # ------------------------------------------------------------------ #
    # Create a scan result **and** fill predicted_label + confidence
    # ------------------------------------------------------------------ #
    async def create_scan_result(self, data: Dict[str, Any]) -> ScanResultModel:
        # 1) Make sure the user exists
        user = await self.user_crud.get_by_id(data["user_id"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 2) Run model inference
        img = _decode_image(data)
        preds = _run_inference(img)

        # 3) Merge predictions into the payload we persist
        payload = {**data, **preds}

        # 4) Persist
        try:
            return await self.scan_crud.create(payload)
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Failed to create scan result")

    # ------------------------------------------------------------------ #
    # Other CRUD helpers (unchanged except for types)
    # ------------------------------------------------------------------ #
    async def get_scan_by_id(self, scan_id: UUID) -> ScanResultModel:
        scan = await self.scan_crud.get_by_id(scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail=f"ScanResult {scan_id} not found")
        return scan

    async def get_scans_by_user(self, user_id: UUID) -> List[ScanResultModel]:
        return await self.scan_crud.get_all_by_field("user_id", user_id)

    async def delete_scan(self, scan_id: UUID) -> None:
        scan = await self.get_scan_by_id(scan_id)
        await self.scan_crud.delete(scan.id)


# Singleton accessor (same pattern you already had)
from functools import lru_cache  # noqa: E402  (re-import for clarity)


@lru_cache()
def get_scan_service(db: DBSessionDep) -> ScanResultService:
    return ScanResultService(
        BaseCRUD(ScanResultModel, db),
        BaseCRUD(UserModel, db),
    )
