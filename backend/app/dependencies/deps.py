from fastapi import Depends, HTTPException, WebSocket, status
from uuid import UUID
from app.clients.supabase_client import SupabaseClient
from fastapi.security import HTTPAuthorizationCredentials
from typing import Annotated
from sqlalchemy.orm import Session
from app.database import get_db
from .auth import verify_jwt

DBSessionDep = Annotated[Session, Depends(get_db)]

CurrentUser = Annotated[dict, Depends(verify_jwt)]

supabase = SupabaseClient().client

async def get_current_user_ws(websocket: WebSocket):
    token = websocket.query_params.get("token") or websocket.headers.get(
        "Authorization", ""
    ).replace("Bearer ", "")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return verify_jwt(creds)
    except HTTPException:
        await websocket.close(code=4401)


async def verify_supabase_ws(ws: WebSocket) -> UUID:
    """
    تستخرج توكن Supabase من رأس Authorization أو من سلسلة الاستعلام ?token=
    وتتحقّق منه لدى Supabase، ثم تعيد user.id عند نجاح التحقّق.
    """
    token = (
        ws.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        or ws.query_params.get("token")
    )

    if not token:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token missing")
        raise HTTPException(status_code=4401, detail="Auth required")

    # Supabase يتحقّق من التوكن ويتأكد من عدم إبطاله أو انتهاء صلاحيته
    resp = supabase.auth.get_user(token)      # :contentReference[oaicite:0]{index=0}
    user = resp.user
    if user is None:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="Bad token")
        raise HTTPException(status_code=4401, detail="Invalid or expired token")

    return UUID(user.id)  
