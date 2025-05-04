from sqlalchemy import Column, UUID, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    image_url = Column(String, nullable=False)
    prediction = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scans")