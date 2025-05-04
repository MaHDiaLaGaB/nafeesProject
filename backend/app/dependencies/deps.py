from fastapi import Depends, HTTPException, WebSocket
from fastapi.security import HTTPAuthorizationCredentials
from typing import Annotated
from sqlalchemy.orm import Session
from database import get_db
from .auth import verify_jwt

DBSessionDep = Annotated[Session, Depends(get_db)]

CurrentUser = Annotated[dict, Depends(verify_jwt)]

async def get_current_user_ws(websocket: WebSocket):
    token = websocket.query_params.get("token") or websocket.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return verify_jwt(creds)
    except HTTPException:
        await websocket.close(code=4401)
