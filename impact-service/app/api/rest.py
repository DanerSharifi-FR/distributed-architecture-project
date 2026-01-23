"""
REST API
========
Endpoints REST pour gérer les impacts météo.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from bson import ObjectId

from app.models.impact import FlightPosition
from app.services.impact_calculator import calculate_impact
from app.services.flight_client import get_flights
from app.services.satellite_client import trigger_satellite_tile
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
async def create_impact(req: PositionRequest, background_tasks: BackgroundTasks):
    """
    Crée un nouvel impact à partir d'une position de vol.
    
    Flow:
    1. Crée l'objet position
    2. Calcule les risques météo
    3. Sauvegarde en MongoDB
    4. Déclenche la génération de tuile satellite (en background)
    5. Retourne l'impact créé
    
    Note: Le satellite-service est appelé APRÈS la sauvegarde car
    il a besoin de récupérer les coordonnées via GET /api/impacts/{id}
    """
    # Créer l'objet position
    position = FlightPosition(
        flight_id=req.flight_id,
        callsign=req.callsign,
        latitude=req.latitude,
        longitude=req.longitude,
        altitude=req.altitude,
        timestamp=datetime.utcnow()
    )
    
    # Calculer l'impact (sans satellite)
    impact = await calculate_impact(position)
    
    # Sauvegarder en MongoDB
    impact_id = ObjectId()
    doc = impact.model_dump()
    doc["_id"] = impact_id
    await get_db().impacts.insert_one(doc)
    
    # Déclencher la génération de tuile satellite (après sauvegarde)
    # Le satellite-service va faire GET /api/impacts/{id} pour récupérer lat/lon
    background_tasks.add_task(trigger_satellite_tile, str(impact_id))
    
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
    """
    Récupère un impact par son ID.
    
    Note: Cet endpoint est aussi utilisé par le satellite-service
    pour récupérer les coordonnées (lat/lon) d'un impact.
    """
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
async def analyze_flights(limit: int = 10, background_tasks: BackgroundTasks = None):
    """
    Analyse les vols en temps réel depuis flight-service.
    
    Flow pour chaque vol:
    1. Calcule l'impact météo
    2. Sauvegarde en MongoDB
    3. Déclenche la génération de tuile satellite
    """
    # Récupérer les vols
    flights = await get_flights()
    
    # Analyser chaque vol
    results = []
    for flight in flights[:limit]:
        # Calculer l'impact
        impact = await calculate_impact(flight)
        
        # Sauvegarder en MongoDB
        impact_id = ObjectId()
        doc = impact.model_dump()
        doc["_id"] = impact_id
        await get_db().impacts.insert_one(doc)
        
        # Déclencher satellite (après sauvegarde)
        if background_tasks:
            background_tasks.add_task(trigger_satellite_tile, str(impact_id))
        else:
            await trigger_satellite_tile(str(impact_id))
        
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
