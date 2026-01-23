"""
MongoDB Connection
==================
Gère la connexion à MongoDB avec Motor (driver async).
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

# Variable globale pour stocker la connexion
db: AsyncIOMotorDatabase = None


async def init_db():
    """Initialise la connexion MongoDB au démarrage de l'app."""
    global db
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.mongo_db]
    print(f"✅ MongoDB connecté: {settings.mongo_db}")


async def close_db():
    """Ferme la connexion MongoDB à l'arrêt de l'app."""
    print("🔌 MongoDB déconnecté")


def get_db() -> AsyncIOMotorDatabase:
    """Retourne la base de données MongoDB."""
    return db


# ============ HELPERS ============

def doc_to_dict(doc: dict) -> dict:
    """
    Convertit un document MongoDB en dict pour l'API.
    
    MongoDB utilise _id (ObjectId), on le convertit en id (string).
    
    Note: On inclut latitude/longitude pour que le satellite-service
    puisse les récupérer via GET /api/impacts/{id}
    """
    position = doc.get("position", {})
    return {
        "id": str(doc["_id"]),
        "flight_id": doc["flight_id"],
        "callsign": doc.get("callsign"),
        "latitude": position.get("latitude"),
        "longitude": position.get("longitude"),
        "altitude": position.get("altitude"),
        "severity": doc["severity"],
        "impact_score": doc["impact_score"],
        "description": doc["description"]
    }
