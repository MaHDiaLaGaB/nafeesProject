from sqlalchemy.orm import Session
from uuid import UUID
from models import ScanResult


def save_scan(db: Session, user_id: UUID, image_url: str, prediction: str):
    scan = ScanResult(user_id=user_id, image_url=image_url, prediction=prediction)
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan
