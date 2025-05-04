from fastapi import APIRouter

from .routers import health, users, scan, chat

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(scan.router, prefix="/scan", tags=["Scan"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
