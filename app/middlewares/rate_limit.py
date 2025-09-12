# app/middleware/rate_limit.py
import time
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, status
from fastapi.responses import JSONResponse

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        redis_client: Optional[object] = None,
        rate_limit: int = 100,
        time_window: int = 60,
        key_prefix: str = "rl",
        exempt_paths: Optional[list] = None,
    ):
        super().__init__(app)
        self._redis = redis_client
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.key_prefix = key_prefix
        self.exempt_paths = exempt_paths or ["/docs", "/openapi.json", "/healthz", "/static"]

    @property
    def redis(self):
        # prefer self._redis, si no, intentar leer app.state.redis
        if self._redis:
            return self._redis
        # getattr because self.app is set by BaseHTTPMiddleware
        return getattr(self.app.state, "redis", None)

    def _key(self, identifier: str) -> str:
        return f"{self.key_prefix}:{identifier}"

    def _identifier(self, request: Request) -> str:
        # si viene token, intenta usarlo (no decodificamos aquí); fallback IP
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
            return f"user:{token}"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host

    async def dispatch(self, request: Request, call_next):
        # excluir paths
        for p in self.exempt_paths:
            if request.url.path.startswith(p):
                return await call_next(request)

        redis = self.redis
        if not redis:
            # si no hay redis disponible, no limitamos (útil para tests/dev)
            return await call_next(request)

        ident = self._identifier(request)
        key = self._key(ident)
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, self.time_window)
        ttl = await redis.ttl(key)

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
