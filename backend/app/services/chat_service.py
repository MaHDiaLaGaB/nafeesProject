# app/services/chat_service.py
from functools import lru_cache
from typing import List
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from crud.base_crud import BaseCRUD
from dependencies import DBSessionDep
from models.chat import Chat as ChatModel


class ChatService:
    def __init__(self, chat_crud: BaseCRUD[ChatModel]):
        self.chat_crud = chat_crud

    async def create_chat(self, customer_id: UUID, merchant_id: UUID) -> ChatModel:
        payload = {"customer_id": customer_id, "merchant_id": merchant_id}
        try:
            return await self.chat_crud.create(payload)
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Failed to create chat")

    async def get_chat_by_id(self, chat_id: UUID) -> ChatModel:
        chat = await self.chat_crud.get_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
        return chat

    async def get_chats_for_customer(self, customer_id: UUID) -> List[ChatModel]:
        return await self.chat_crud.get_all_by_field("customer_id", customer_id)

    async def get_chats_for_merchant(self, merchant_id: UUID) -> List[ChatModel]:
        return await self.chat_crud.get_all_by_field("merchant_id", merchant_id)

    async def delete_chat(self, chat_id: UUID) -> None:
        chat = await self.get_chat_by_id(chat_id)
        await self.chat_crud.delete(chat.id)


@lru_cache()
def get_chat_service(db: DBSessionDep) -> ChatService:
    return ChatService(BaseCRUD(ChatModel, db))
