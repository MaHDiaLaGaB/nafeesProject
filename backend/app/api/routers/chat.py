# app/api_v1/chat.py
from typing import Dict, List
from uuid import UUID
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
)

from app.dependencies.deps import CurrentUser
from app.dependencies.auth import role_required
from app.dependencies.deps import get_current_user_ws, verify_supabase_ws
from app.services.chat_service import get_chat_service, ChatService
from app.services.message_service import get_message_service, MessageService
from app.schemas.chat import ChatCreate, MessageOut, ChatMessageIn, ChatMessageOut
from app.logger import get_logger

logger = get_logger()

router = APIRouter()


# ---- HTTP endpoints for creating/fetching chats ----


@router.post("/create-chat", summary="Start a new conversation")
async def create_chat(
    payload: ChatCreate,
    current_user: dict = Depends(role_required("customer")),
    svc: ChatService = Depends(get_chat_service),
):
    return await svc.create_chat(str(current_user["id"]), str(payload.merchant_id))


@router.get(
    "/get/{chat_id}",
    summary="Get a conversation by ID",
    dependencies=[Depends(role_required("customer", "merchant"))],
)
async def read_chat(chat_id: UUID, svc: ChatService = Depends(get_chat_service)):
    return await svc.get_chat_by_id(chat_id)


@router.get(
    "/get/{chat_id}/messages",
    summary="List all messages in a conversation",
    dependencies=[Depends(role_required("customer", "merchant"))],
)
async def read_messages(
    chat_id: UUID, msg_svc: MessageService = Depends(get_message_service)
):
    return [
        MessageOut.model_validate(m).model_dump()
        for m in await msg_svc.get_messages_for_chat(chat_id)
    ]


# ---- WebSocket for live two‐way chat ----


class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}

    async def connect(self, room: str, ws: WebSocket):
        logger.info(f"WebSocket connection established for room: {room}")
        await ws.accept()
        logger.info(f"WebSocket accepted for room: {room}")
        self.active.setdefault(room, []).append(ws)

    def disconnect(self, room: str, ws: WebSocket):
        logger.info(f"WebSocket disconnected from room: {room}")
        self.active[room].remove(ws)
        if not self.active[room]:
            del self.active[room]

    async def broadcast(self, room: str, msg: dict):
        for conn in self.active.get(room, []):
            await conn.send_json(msg)


manager = ConnectionManager()

@router.websocket("/ws/chat/{room_id}")
async def chat_ws(ws: WebSocket, room_id: UUID):
    user_id = await verify_supabase_ws(ws)       # ← هنا التوثيق عبر Supabase
    await manager.connect(room_id, ws)

    try:
        while True:
            data = await ws.receive_json()
            msg_in  = ChatMessageIn(**data)
            msg_out = ChatMessageOut(
                **msg_in.dict(),
                sender_id=user_id,
                sent_at=datetime.utcnow(),
            )
            await manager.broadcast(room_id, msg_out.dict())
    except WebSocketDisconnect:
        manager.disconnect(room_id, ws)


@router.websocket("/ws/{chat_id}")
async def websocket_chat(
    chat_id: UUID,
    websocket: WebSocket,
    current_user: dict = Depends(get_current_user_ws),
    chat_svc: ChatService = Depends(get_chat_service),
    msg_svc: MessageService = Depends(get_message_service),
):
    # if get_current_user_ws already closed the socket on bad token, we bail
    logger.info(f"WebSocket connection attempt for chat {chat_id} by user {current_user}")
    if not current_user:
        return

    # ensure they belong
    chat = await chat_svc.get_chat_by_id(chat_id)
    logger.info(f"Chat retrieved: {chat}")
    try:
        user_uuid = UUID(current_user["id"])
        logger.info(f"Current user UUID: {user_uuid}")
    except ValueError:
        await websocket.close(code=1008)
        return

    if user_uuid not in {chat.customer_id, chat.merchant_id}:
        logger.warning(f"User {current_user['id']} not authorized for chat {chat_id}")

        await websocket.close(code=1008)
        return  

    room = str(chat_id)
    logger.info(f"Connecting user {current_user['id']} to room {room}")
    await manager.connect(room, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"Received data: {data}")
            payload = {
                "conversation_id": chat_id,
                "sender_id": current_user["id"],
                **data,
            }
            msg = await msg_svc.send_message(payload)
            logger.info(f"Message sent: {msg}")
            out = MessageOut.model_validate(msg).model_dump()
            logger.info(f"Broadcasting message: {out}")
            await manager.broadcast(room, out)
    except WebSocketDisconnect:
        manager.disconnect(room, websocket)
    except Exception as e:
        logger.error(f"Error occurred: {e}")    
        await websocket.close(code=1011)
