# app/db/mongodb.py

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import config

# Одоо config.MONGO_URI-аас холбох URL-ийг авна
client = AsyncIOMotorClient(config.MONGO_URI)
db = client[config.MONGO_DB_NAME]

async def get_db():
    return db
