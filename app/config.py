# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))

    SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")

    RATE_LIMIT = int(os.getenv("RATE_LIMIT", 100))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))

settings = Settings()
