"""
Satellite Client
================
Client pour déclencher la génération de tuiles satellite.

Le satellite-service attend un impact_id et récupère lui-même
les coordonnées depuis notre API /api/impacts/{impact_id}.

IMPORTANT: On appelle ce service APRÈS avoir créé l'impact en base,
car le satellite-service va faire un GET sur notre API pour récupérer
les coordonnées (lat/lon) de l'impact.
"""

import httpx
from app.config import get_settings


async def trigger_satellite_tile(impact_id: str) -> bool:
    """
    Déclenche la génération d'une tuile satellite pour un impact.
    
    Args:
        impact_id: ID de l'impact (ObjectId MongoDB)
    
    Returns:
        True si l'appel a réussi, False sinon
    
    Note:
        - Utilise PUT car on déclenche une action (génération de tuile)
        - Le satellite-service récupère lat/lon via GET /api/impacts/{impact_id}
        - On n'attend pas de données en retour, juste une confirmation
    """
    settings = get_settings()
    
    if settings.use_mock_satellite:
        print(f"🛰️ [MOCK] Satellite tile triggered for impact {impact_id}")
        return True
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.put(
                f"{settings.satellite_service_url}/satellites/tiles/impacts/{impact_id}"
            )
            response.raise_for_status()
            print(f"🛰️ Satellite tile generated for impact {impact_id}")
            return True
        except Exception as e:
            print(f"⚠️ Satellite service error: {e}")
            return False
