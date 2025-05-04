from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from clients.supabase_client import SupabaseClient
from logger import get_logger

logger = get_logger("auth")
security = HTTPBearer()
supabase = SupabaseClient().client


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify the JWT token and retrieve the user information.
    """
    logger.info(f"the credentials {credentials}")
    token = credentials.credentials
    try:
        # Retrieve the user from Supabase
        response = supabase.auth.get_user(token)
        user = response.user

        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Extract role from user's metadata
        resp = user.model_dump()  # Assuming user is a Pydantic model
        logger.info(f"the user info {resp}, {type(resp)}")
        role = resp.get("user_metadata", {}).get("role")
        if not role:
            raise HTTPException(status_code=403, detail="Role not assigned to the user")

        return {
            "id": resp["id"],
            "email": resp["email"],
            "role": role,
        }
    except Exception as e:
        raise HTTPException(
            status_code=401, detail=f"Token verification failed: {str(e)}"
        ) from e


def role_required(*allowed_roles: str):
    def wrapper(user=Depends(verify_jwt)):
        if user["role"] not in allowed_roles and user["role"] != "superadmin":
            raise HTTPException(403, "Insufficient role privileges")
        return user
    return wrapper
