"""
REST API
========
Endpoints REST pour gérer les impacts météo.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId

from app.models.impact import FlightPosition
from app.services.impact_calculator import calculate_impact
from app.services.flight_client import get_flights
from app.db.mongodb import get_db, doc_to_dict

router = APIRouter(prefix="/api", tags=["impacts"])


# ============ SCHEMAS (request/response) ============

class PositionRequest(BaseModel):
    """Données pour créer un impact."""
    flight_id: str
    latitude: float
    longitude: float
    altitude: float
    callsign: Optional[str] = None


# ============ ROUTES ============

@router.get("/health")
async def health():
    """Vérifie que le service et MongoDB fonctionnent."""
    try:
        await get_db().impacts.find_one()
        return {"status": "ok", "mongo": True}
    except:
        return {"status": "error", "mongo": False}


@router.post("/impacts", status_code=201)
async def create_impact(req: PositionRequest):
    """
    Crée un nouvel impact à partir d'une position de vol.
    
    1. Génère un ObjectId en avance (pour le satellite-service)
    2. Reçoit une position (lat, lon, altitude)
    3. Calcule les risques météo et satellite
    4. Sauvegarde en base avec l'ID pré-généré
    5. Retourne l'impact créé
    """
    # Générer l'ObjectId en avance
    # Le satellite-service en a besoin pour nous rappeler via /api/impacts/{id}
    impact_id = ObjectId()
    
    # Créer l'objet position
    position = FlightPosition(
        flight_id=req.flight_id,
        callsign=req.callsign,
        latitude=req.latitude,
        longitude=req.longitude,
        altitude=req.altitude,
        timestamp=datetime.utcnow()
    )
    
    # Calculer l'impact (on passe l'ID pré-généré)
    impact = await calculate_impact(position, str(impact_id))
    
    # Sauvegarder en MongoDB avec l'ID pré-généré
    doc = impact.model_dump()
    doc["_id"] = impact_id  # Utiliser l'ID qu'on a généré
    await get_db().impacts.insert_one(doc)
    
    # Retourner l'impact créé
    return {
        "id": str(impact_id),
        "flight_id": impact.flight_id,
        "callsign": impact.callsign,
        "severity": impact.severity.value,
        "impact_score": impact.impact_score,
        "description": impact.description
    }


@router.get("/impacts")
async def list_impacts(limit: int = 50):
    """Liste tous les impacts (limité à 50 par défaut)."""
    cursor = get_db().impacts.find().limit(limit)
    return [doc_to_dict(doc) async for doc in cursor]


@router.get("/impacts/{impact_id}")
async def get_impact(impact_id: str):
    """Récupère un impact par son ID."""
    doc = await get_db().impacts.find_one({"_id": ObjectId(impact_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Impact non trouvé")
    return doc_to_dict(doc)


@router.delete("/impacts/{impact_id}")
async def delete_impact(impact_id: str):
    """Supprime un impact."""
    result = await get_db().impacts.delete_one({"_id": ObjectId(impact_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Impact non trouvé")
    return {"deleted": True}


@router.post("/analyze-flights")
async def analyze_flights(limit: int = 10):
    """
    Analyse les vols en temps réel depuis flight-service.
    
    1. Récupère les vols actuels depuis flight-service
    2. Génère un ObjectId pour chaque impact
    3. Calcule l'impact pour chaque vol (avec l'ID pré-généré)
    4. Sauvegarde tous les impacts
    """
    # Récupérer les vols
    flights = await get_flights()
    
    # Analyser chaque vol
    results = []
    for flight in flights[:limit]:
        # Générer l'ObjectId en avance pour le satellite-service
        impact_id = ObjectId()
        
        impact = await calculate_impact(flight, str(impact_id))
        doc = impact.model_dump()
        doc["_id"] = impact_id  # Utiliser l'ID pré-généré
        await get_db().impacts.insert_one(doc)
        
        results.append({
            "id": str(impact_id),
            "flight_id": impact.flight_id,
            "severity": impact.severity.value,
            "impact_score": impact.impact_score
        })
    
    return {"analyzed": len(results), "impacts": results}


@router.get("/stats")
async def stats():
    """Statistiques sur les impacts."""
    count = await get_db().impacts.count_documents({})
    return {"total": count}
