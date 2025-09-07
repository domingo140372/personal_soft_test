# app/middleware/rate_limit.py
import time
from typing import Optional
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as redis
import jwt
from app.config import settings


def default_identifier(request: Request):
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass
    forward = request.headers.get("X-Forwarded-For")
    if forward:
        return forward.split(",")[0].strip()
    return request.client.host


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.rate_limit = settings.RATE_LIMIT
        self.time_window = settings.RATE_LIMIT_WINDOW
        self.key_prefix = "rl"
        self.exempt_paths = ["/docs", "/openapi.json", "/healthz"]

    def _key(self, identifier: str):
        return f"{self.key_prefix}:{identifier}"

    async def dispatch(self, request: Request, call_next):
        for p in self.exempt_paths:
            if request.url.path.startswith(p):
                return await call_next(request)

        ident = default_identifier(request)
        key = self._key(ident)

        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, self.time_window)

        ttl = await self.redis.ttl(key)
        if current > self.rate_limit:
            reset_ts = int(time.time()) + (ttl if ttl and ttl > 0 else self.time_window)
            body = {
                "status": "error",
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests",
                    "details": f"Allowed {self.rate_limit} per {self.time_window} seconds",
                    "reset_at": reset_ts
                }
            }
            return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=body)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.rate_limit - int(current)))
        response.headers["X-RateLimit-Reset"] = str(ttl)
        return response
