from sqlalchemy.orm import Session
from uuid import UUID
from crud.base_crud import BaseCRUD
from models import Chat, Message
from schemas.chat import MessageCreate

class ConversationCRUD(BaseCRUD[Chat]):
    pass

class MessageCRUD(BaseCRUD[Message]):
    pass

def create_conversation(db: Session, customer_id: UUID, merchant_id: UUID):
    crud = ConversationCRUD(Chat, db)
    return db.sync_session  # placeholder for BaseCRUD create (sync override)

# Simpler explicit functions (async not needed)

def list_conversations(db: Session, user_id: UUID):
    return db.query(Chat).filter((Chat.customer_id == user_id) | (Chat.merchant_id == user_id)).all()

def create_message(db: Session, payload: MessageCreate, sender_id: UUID, image_url: str | None = None):
    msg = Message(
        conversation_id=payload.conversation_id,
        sender_id=sender_id,
        content=payload.content,
        image_url=image_url,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def list_messages(db: Session, conversation_id: UUID):
    return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()