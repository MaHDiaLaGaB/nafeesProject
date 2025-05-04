from sqlalchemy import Column, ForeignKey, Text, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chat.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=True)              # نص
    image_url = Column(String, nullable=True)          # رابط الصورة المرفقـة (اختياري)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages_sent")
