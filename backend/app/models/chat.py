from sqlalchemy import Column, ForeignKey, DateTime, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base


class Chat(Base):
    __tablename__ = "chat"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("User", back_populates="conversations_as_customer", foreign_keys=[customer_id])
    merchant = relationship("User", back_populates="conversations_as_merchant", foreign_keys=[merchant_id])
    messages = relationship(
    "Message",
    back_populates="conversation",    # ← was "chat"
    cascade="all, delete"
)
