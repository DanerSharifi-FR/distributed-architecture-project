from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.config import get_settings
from app.models.impact import Impact


_client: AsyncIOMotorClient | None = None


async def init_db():
    """Initialise la connexion MongoDB et Beanie."""
    global _client
    
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongo_url)
    
    await init_beanie(
        database=_client[settings.mongo_db],
        document_models=[Impact],
    )
    
    print(f"✅ Connected to MongoDB: {settings.mongo_url}/{settings.mongo_db}")


async def close_db():
    """Ferme la connexion MongoDB."""
    global _client
    if _client:
        _client.close()
        print("🔌 MongoDB connection closed")
