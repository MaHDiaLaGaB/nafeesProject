from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ChatMessageIn(BaseModel):
    content: str

class ChatMessageOut(ChatMessageIn):
    sender_id: UUID
    sent_at: datetime

class MessageBase(BaseModel):
    content: str | None = None
    image_url: str | None = None


class MessageCreate(MessageBase):
    conversation_id: UUID


class MessageOut(MessageBase):
    id: UUID
    sender_id: UUID
    created_at: datetime

    class ConfigDict:
        from_attributes = True


class ChatCreate(BaseModel):
    merchant_id: UUID


class ChatOut(BaseModel):
    id: UUID
    merchant_id: UUID
    customer_id: UUID
    created_at: datetime

    class ConfigDict:
        from_attributes = True
