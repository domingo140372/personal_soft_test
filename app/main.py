# app/main.py
from fastapi import FastAPI
from redis.asyncio import Redis

from .config import settings
from .database import create_db_and_tables
from .middleware.rate_limit import RedisRateLimitMiddleware
from .routes import init_routes

# Crear app
app = FastAPI(title="Api_MENSAJES", version="2.0.0")

# Registrar middleware antes de arrancar; redis_client=None por ahora
app.add_middleware(
    RedisRateLimitMiddleware,
    redis_client=None,
    rate_limit=settings.RATE_LIMIT,
    time_window=settings.RATE_LIMIT_WINDOW,
)

# Registrar rutas (users, messages, auth)
init_routes(app)

# Eventos lifecycle
@app.on_event("startup")
async def on_startup():
    # Crear tablas en BD
    create_db_and_tables()

    # Conectar Redis y guardarlo en app.state
    app.state.redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)

    # Inyectar redis_client en el middleware ya registrado
    for mw in app.user_middleware:
        if "redis_client" in mw.options and mw.options["redis_client"] is None:
            mw.options["redis_client"] = app.state.redis

@app.on_event("shutdown")
async def on_shutdown():
    if hasattr(app.state, "redis"):
        try:
            await app.state.redis.close()
        except Exception:
            pass
