"""
REST API
========
Endpoints REST pour gérer les impacts météo.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from bson import ObjectId

from app.services.impact_calculator import calculate_impact
from app.services.flight_client import get_flights
from app.services.satellite_client import trigger_satellite_tile
from app.db.mongodb import get_db, doc_to_dict

router = APIRouter(prefix="/api", tags=["impacts"])


# ============ ROUTES ============

@router.get("/health")
async def health():
    """Vérifie que le service et MongoDB fonctionnent."""
    try:
        await get_db().impact.find_one()
        return {"status": "ok", "mongo": True}
    except:
        return {"status": "error", "mongo": False}


@router.post("/impacts", status_code=201)
async def create_impacts(limit: int = 10, background_tasks: BackgroundTasks = None):
    """
    Analyse les vols en temps réel depuis flight-service et crée des impacts.
    
    Flow:
    1. Récupère les vols depuis flight-service (Bastien)
    2. Pour chaque vol: calcule l'impact météo
    3. Sauvegarde en MongoDB
    4. Déclenche satellite-service (Thomas) pour générer les tuiles
    
    Paramètre:
    - limit: nombre de vols à analyser (défaut: 10)
    """
    # Récupérer les vols depuis flight-service
    flights = await get_flights()
    
    # Analyser chaque vol
    results = []
    for flight in flights[:limit]:
        # Calculer l'impact météo
        impact = await calculate_impact(flight)
        
        # Sauvegarder en MongoDB
        impact_id = ObjectId()
        doc = impact.model_dump()
        doc["_id"] = impact_id
        await get_db().impact.insert_one(doc)
        
        # Déclencher satellite-service (après sauvegarde)
        if background_tasks:
            background_tasks.add_task(trigger_satellite_tile, str(impact_id))
        else:
            await trigger_satellite_tile(str(impact_id))
        
        results.append({
            "id": str(impact_id),
            "flight_id": impact.flight_id,
            "callsign": impact.callsign,
            "severity": impact.severity.value,
            "impact_score": impact.impact_score
        })
    
    return {"analyzed": len(results), "impacts": results}


@router.get("/impacts")
async def list_impacts(limit: int = 50):
    """Liste tous les impacts (limité à 50 par défaut)."""
    cursor = get_db().impact.find().limit(limit)
    return [doc_to_dict(doc) async for doc in cursor]


@router.get("/impacts/{impact_id}")
async def get_impact(impact_id: str):
    """
    Récupère un impact par son ID.
    
    Note: Cet endpoint est aussi utilisé par le satellite-service
    pour récupérer les coordonnées (lat/lon) d'un impact.
    """
    doc = await get_db().impact.find_one({"_id": ObjectId(impact_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Impact non trouvé")
    return doc_to_dict(doc)


@router.delete("/impacts/{impact_id}")
async def delete_impact(impact_id: str):
    """Supprime un impact."""
    result = await get_db().impact.delete_one({"_id": ObjectId(impact_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Impact non trouvé")
    return {"deleted": True}


@router.get("/stats")
async def stats():
    """Statistiques sur les impacts."""
    count = await get_db().impact.count_documents({})
    return {"total": count}
