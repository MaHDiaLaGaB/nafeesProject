from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

# ───── رسائل حيّة (WebSocket) ──────────────────────────────────────────────
class ChatMessageIn(BaseModel):
    content: str
    image_url: str | None = None


class ChatMessageOut(ChatMessageIn):
    sender_id: UUID
    sent_at: datetime


# ───── رسائل محفوظة في DB ──────────────────────────────────────────────────
class MessageBase(BaseModel):
    content: str | None = None
    image_url: str | None = None


class MessageCreate(MessageBase):
    chat_id: UUID


class MessageOut(MessageBase):
    id: UUID
    chat_id: UUID
    sender_id: UUID
    created_at: datetime

    # ORM-mode for Pydantic v2
    model_config = ConfigDict(from_attributes=True)


# ───── المحادثة (Chat) ─────────────────────────────────────────────────────
class ChatCreate(BaseModel):
    merchant_id: UUID


class ChatOut(BaseModel):
    id: UUID
    merchant_id: UUID
    customer_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
