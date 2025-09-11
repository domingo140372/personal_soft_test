#### Archivo de rutas principal

from fastapi import FastAPI
from app.users.route import router as users_router
from app.messages.route import router as messages_router

def init_routes(app: FastAPI):
    app.include_router(users_router, prefix="/users", tags=["Users"])
    app.include_router(messages_router, prefix="/messages", tags=["Messages"])
