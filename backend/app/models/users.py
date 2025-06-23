from sqlalchemy import Column, String, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum, uuid, datetime as dt

from app.database import Base


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
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superadmin = Column(Boolean, default=False, nullable=False)
    is_merchant = Column(Boolean, default=False, nullable=False)
    is_customer = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    # inverse side of UploadedImage.user
    images = relationship(
        "UploadedImage",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # other relationships...
    conversations_as_customer = relationship(
        "Chat", back_populates="customer", foreign_keys="Chat.customer_id"
    )
    conversations_as_merchant = relationship(
        "Chat", back_populates="merchant", foreign_keys="Chat.merchant_id"
    )
    messages_sent = relationship("Message", back_populates="sender")
    scans = relationship("ScanResult", back_populates="user")
