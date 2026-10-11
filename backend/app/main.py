from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, sessions
from app.core.config import settings

from app.api import chat
from app.core.config import settings

from sqlalchemy import text
from app.db.session import engine

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="AI 私人教练 · 多 Agent 协作健身规划系统",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(auth.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


@app.get("/health/db", tags=["system"])
async def health_db():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        value = result.scalar()
    return {"status": "ok", "db": "postgres", "result": value}