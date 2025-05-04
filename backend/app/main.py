# app/main.py
from __future__ import annotations

import threading
import uvicorn
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from database import Base, engine
from api.endpoints import api_router
from clients.supabase_client import SupabaseClient
from logger import get_logger

logger = get_logger(__name__)

# ------------------------------------------------------------------
# 1) تحميل متغيّرات البيئة
# ------------------------------------------------------------------
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path, override=True)

@asynccontextmanager
async def lifespan(app):
    """
    Runs once before the app starts handling requests,
    and once after it stops.
    """
    # --- Startup logic ---
    # Create tables (if not exist)
    Base.metadata.create_all(bind=engine)

    # e.g. ensure a superadmin exists
    # SupabaseClient().ensure_superadmin()
    try:
        yield  # <<< CONTROL RETURNS TO FASTAPI
    finally:
        # --- Shutdown logic ---
        # Place any cleanup here (close DB pools, flush logs, etc.)
        logger.info("Checking active threads during shutdown...")
        for thread in threading.enumerate():
            logger.info(f"Thread still running: {thread.name}")
        engine.dispose()

        logger.info("Shutdown complete.")



# ------------------------------------------------------------------
# 3) FastAPI Application
# ------------------------------------------------------------------
app = FastAPI(
    title="Gem Classifier & Chat",
    version="1.0.0",
    docs_url="/docs",           # يمكن تخصيص مسار التوثيق
    redoc_url=None,
    lifespan=lifespan)

# ------------------------------------------------------------------
# 4) CORS (عدِّله في الإنتاج)
# ------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
# ------------------------------------------------------------------
# 6) Routers
# ------------------------------------------------------------------
API_PREFIX = "/api"
app.include_router(api_router)
# Tell FastAPI to use our generator
client = SupabaseClient()
client.ensure_superadmin()
client.sign_in(email=settings.SUPERADMIN_EMAIL, password=settings.SUPERADMIN_PASSWORD)

# ------------------------------------------------------------------
# Ready!
# ------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=9213, timeout_graceful_shutdown=5)
