# app/routes.py
from fastapi import FastAPI
from app.users.routes import router as users_router
from app.messages.routes import router as messages_router
from app.users.auth import router as auth_router

def init_routes(app: FastAPI):
    # mantén token en la raíz: POST /token (si prefieres otro prefijo cambia aquí)
    app.include_router(auth_router, prefix="", tags=["Auth"])
    app.include_router(users_router, prefix="/users", tags=["Users"])
    app.include_router(messages_router, prefix="/messages", tags=["Messages"])
