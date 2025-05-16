from motor.motor_asyncio import AsyncIOMotorClient

from app.core.configs import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
mongo_db = client[settings.MONGO_DB]
