# app/api_v1/chat.py
from typing import Dict, List
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
)

from dependencies.deps import CurrentUser
from dependencies.auth import role_required
from services.chat_service import get_chat_service, ChatService
from services.message_service import get_message_service, MessageService
from schemas.chat import ChatCreate, MessageOut

router = APIRouter()


# ---- HTTP endpoints for creating/fetching chats ----

@router.post(
        "/create-chat", 
        summary="Start a new conversation",
        dependencies=[Depends(role_required("customer"))],)
async def create_chat(
    payload: ChatCreate,
    current_user: CurrentUser,
    svc: ChatService = Depends(get_chat_service),
):
    # optionally enforce that current_user.id == payload.customer_id
    return await svc.create_chat(payload.customer_id, payload.merchant_id)


@router.get(
        "/get/{chat_id}", 
        summary="Get a conversation by ID",
        dependencies=[Depends(role_required("customer", "merchant"))])
async def read_chat(
    chat_id: UUID, svc: ChatService = Depends(get_chat_service)
):
    return await svc.get_chat_by_id(chat_id)


@router.get(
    "/get/{chat_id}/messages",
    summary="List all messages in a conversation",
    dependencies=[Depends(role_required("customer", "merchant"))]
)
async def read_messages(
    chat_id: UUID, msg_svc: MessageService = Depends(get_message_service)
):
    return [MessageOut.model_validate(m).model_dump() for m in await msg_svc.get_messages_for_chat(chat_id)]



# ---- WebSocket for live two‐way chat ----

class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}

    async def connect(self, room: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(room, []).append(ws)

    def disconnect(self, room: str, ws: WebSocket):
        self.active[room].remove(ws)
        if not self.active[room]:
            del self.active[room]

    async def broadcast(self, room: str, msg: dict):
        for conn in self.active.get(room, []):
            await conn.send_json(msg)


manager = ConnectionManager()


@router.websocket("/ws/{chat_id}")
async def websocket_chat(
    chat_id: UUID,
    websocket: WebSocket,
    current_user: CurrentUser,
    chat_svc: ChatService = Depends(get_chat_service),
    msg_svc: MessageService = Depends(get_message_service),
):
    # 1) verify chat exists & that user is allowed
    chat = await chat_svc.get_chat_by_id(chat_id)
    if current_user.id not in {chat.customer_id, chat.merchant_id}:
        await websocket.close(code=1008)
        return

    room = str(chat_id)
    await manager.connect(room, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            # expect: {"content": "...", "image_url": None}
            payload = {
                "conversation_id": chat_id,
                "sender_id": current_user.id,
                **data,
            }
            msg = await msg_svc.send_message(payload)
            # Pydantic v2: validate from ORM and dump to dict
            out = MessageOut.model_validate(msg).model_dump()
            await manager.broadcast(room, out)
    except WebSocketDisconnect:
        manager.disconnect(room, websocket)
    except Exception:
        await websocket.close(code=1011)
