import enum, uuid
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class UserRole(str, enum.Enum):
    merchant = "merchant"
    customer = "customer"
    superadmin = "superadmin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.customer, nullable=False)

    # علاقات
    conversations_as_customer = relationship("Chat", back_populates="customer", foreign_keys="Chat.customer_id")
    conversations_as_merchant = relationship("Chat", back_populates="merchant", foreign_keys="Chat.merchant_id")
    messages_sent = relationship("Message", back_populates="sender")
    scans = relationship("ScanResult", back_populates="user")