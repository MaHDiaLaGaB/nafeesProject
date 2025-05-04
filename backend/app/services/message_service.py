# app/services/message_service.py
from functools import lru_cache
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from crud.base_crud import BaseCRUD
from dependencies import DBSessionDep
from models.message import Message as MessageModel


class MessageService:
    def __init__(self, msg_crud: BaseCRUD[MessageModel]):
        self.msg_crud = msg_crud

    async def send_message(self, data: Dict[str, Any]) -> MessageModel:
        """
        data should contain:
         - conversation_id
         - sender_id
         - content or image_url
        """
        try:
            return await self.msg_crud.create(data)
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Failed to send message")

    async def get_message_by_id(self, msg_id: UUID) -> MessageModel:
        msg = await self.msg_crud.get_by_id(msg_id)
        if not msg:
            raise HTTPException(status_code=404, detail=f"Message {msg_id} not found")
        return msg

    async def get_messages_for_chat(self, conversation_id: UUID) -> List[MessageModel]:
        return await self.msg_crud.get_all_by_field("conversation_id", conversation_id)

    async def delete_message(self, msg_id: UUID) -> None:
        await self.msg_crud.delete(msg_id)


@lru_cache()
def get_message_service(db: DBSessionDep) -> MessageService:
    return MessageService(BaseCRUD(MessageModel, db))
