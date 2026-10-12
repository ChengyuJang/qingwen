"""基于 Redis 的 IP 限流中间件。

策略：固定窗口计数器。窗口内超过上限返回 429。
- 普通接口：120 次/分钟/IP
- LLM 接口（/api/chat/stream）：10 次/分钟/IP
- 登录/注册：更严格，防暴力破解

Redis 挂掉时降级为放行（记录 warning），避免限流组件拖垮整个服务。
"""
import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.redis import get_redis

logger = structlog.get_logger("rate_limit")

# path 前缀 -> (窗口秒数, 最大请求数)
RULES: list[tuple[str, int, int]] = [
    ("/api/chat/stream", 60, 10),
    ("/api/auth/login", 60, 10),
    ("/api/auth/register", 60, 5),
]
DEFAULT_WINDOW = 60
DEFAULT_MAX = 120

WHITELIST_PREFIXES = ("/health", "/docs", "/redoc", "/openapi.json")


def _pick_rule(path: str) -> tuple[int, int]:
    for prefix, window, limit in RULES:
        if path.startswith(prefix):
            return window, limit
    return DEFAULT_WINDOW, DEFAULT_MAX


def _client_ip(request: Request) -> str:
    # 若经反向代理，优先 X-Forwarded-For 的第一段
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if any(path.startswith(p) for p in WHITELIST_PREFIXES):
            return await call_next(request)

        window, limit = _pick_rule(path)
        key = f"rl:{path}:{_client_ip(request)}"

        redis = get_redis()
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window)
        except Exception as e:
            # Redis 挂了不影响主流程
            logger.warning("rate_limit_redis_unavailable", error=str(e))
            return await call_next(request)

        if count > limit:
            ttl = await redis.ttl(key)
            retry_after = max(int(ttl), 1)
            logger.info(
                "rate_limited",
                path=path,
                ip=_client_ip(request),
                count=count,
                limit=limit,
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "code": 10005,
                    "message": f"请求过于频繁，请 {retry_after} 秒后重试",
                },
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        # 把剩余额度写进 header，方便前端显示
        remaining = max(limit - count, 0)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response