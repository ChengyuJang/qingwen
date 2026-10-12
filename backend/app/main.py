from contextlib import asynccontextmanager
from app.middleware.rate_limit import RateLimitMiddleware

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import auth, chat, logs, plans, sessions, weight
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.session import engine
from app.middleware.logging import RequestLoggingMiddleware
from app.core.redis import close_redis

configure_logging()
logger = get_logger("startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting", env=settings.ENV, debug=settings.DEBUG)
    yield
    await close_redis()
    logger.info("app_stopped")



app = FastAPI(
    title=settings.APP_NAME,
    version="0.3.0",
    description=(
        "**轻问** · AI 私人教练 · 多 Agent 协作健身规划系统\n\n"
        "## 功能模块\n"
        "- **auth**：注册、登录、JWT 认证\n"
        "- **chat**：SSE 流式对话（Orchestrator + 4 专家 Agent）\n"
        "- **sessions**：会话管理\n"
        "- **plans**：训练/营养/恢复规划查询\n"
        "- **logs**：每日打卡\n"
        "- **weight**：体重记录 + 趋势\n"
        "- **system**：健康检查\n\n"
        "## 认证方式\n"
        "登录后拿到 `access_token`，在右上角 **Authorize** 里粘贴，"
        "之后所有需要认证的接口都会自动带上 `Bearer` 头。"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "注册、登录、当前用户"},
        {"name": "chat", "description": "**SSE 流式对话**，多 Agent 协作入口"},
        {"name": "sessions", "description": "会话 CRUD"},
        {"name": "plans", "description": "训练/营养/恢复规划查询"},
        {"name": "logs", "description": "每日打卡（训练/饮食/睡眠/心情）"},
        {"name": "weight", "description": "体重记录与趋势"},
        {"name": "system", "description": "健康检查与探活"},
    ],
)

# 中间件执行顺序（外 → 内）：
#   Logging → RateLimit → CORS → 路由
# 先 add 的在内层，后 add 的在外层
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
register_exception_handlers(app)

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(auth.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(weight.router, prefix="/api")
app.include_router(plans.router, prefix="/api")


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


@app.get("/health/db", tags=["system"])
async def health_db():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        value = result.scalar()
    return {"status": "ok", "db": "postgres", "result": value}