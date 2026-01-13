from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import get_settings
from app.models.impact import Impact

_client = None

async def init_db():
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongo_url)
    await init_beanie(database=_client[settings.mongo_db], document_models=[Impact])

async def close_db():
    global _client
    if _client:
        _client.close()
