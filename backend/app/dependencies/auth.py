# app/dependencies/auth.py
import os
from uuid import UUID
from typing import Annotated, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.users import User  # تأكد من المسار الصحيح لموديل المستخدمين
from app.clients.supabase_client import SupabaseClient
from app.logger import get_logger

logger = get_logger()

security = HTTPBearer(auto_error=False)
supabase = SupabaseClient().client

DISABLE_AUTH = os.getenv("DISABLE_AUTH", "false").lower() == "true"
DEFAULT_ROLE = os.getenv("DEFAULT_ROLE", "customer")  # في حال المستخدم مش موجود في DB

DBSessionDep = Annotated[Session, Depends(get_db)]

def _dev_user() -> dict:
    # مستخدم وهمي عند تعطيل الأمانcd 
    return {
        "id": os.getenv("DEV_USER_ID", "00000000-0000-0000-0000-000000000000"),
        "email": os.getenv("DEV_EMAIL", "dev@example.com"),
        "role": os.getenv("DEV_ROLE", "customer"),
    }

def verify_jwt(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: DBSessionDep = None,
):
    """
    يتحقّق من صلاحية التوكن عبر Supabase للحصول على الـ id/email فقط،
    ثم يجلب الدور من جدول users في قاعدة البيانات.
    """
    if DISABLE_AUTH:
        return _dev_user()

    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = credentials.credentials
    try:
        # 1) نتحقّق من التوكن عند Supabase ونستخرج الـ id/email
        resp = supabase.auth.get_user(token)
        user_obj = resp.user
        if not user_obj:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_dump = user_obj.model_dump()  # Pydantic -> dict
        user_id = str(user_dump["id"])
        user_email = user_dump.get("email")

        # 2) نجيب الدور من قاعدة البيانات (users.role)
        # تأكد إن نوع العمود id في جدولك يتوافق (UUID أو نص)
        db_user = db.query(User).filter(User.id == user_id).first()
        role = (db_user.role if db_user and getattr(db_user, "role", None) else DEFAULT_ROLE)

        logger.info(f"Auth OK: id={user_id}, email={user_email}, role={role}")

        return {"id": user_id, "email": user_email, "role": role}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Token verification failed")
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}") from e


def role_required(*allowed_roles: str):
    """
    يسمح بالدخول إذا كان دور المستخدم ضمن المسموح به أو كان Superadmin.
    """
    def wrapper(user=Depends(verify_jwt)):
        role = user.get("role")
        if role == "superadmin" or role in allowed_roles:
            return user
        raise HTTPException(status_code=403, detail="Insufficient role privileges")
    return wrapper

