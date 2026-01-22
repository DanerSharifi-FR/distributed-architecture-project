"""
Satellite Client
================
Client pour récupérer le contexte satellite.

Le satellite-service attend un impact_id et récupère lui-même
les coordonnées depuis notre API /api/impacts/{impact_id}.
"""

import random
import httpx
from datetime import datetime
from app.models.impact import SatelliteContext
from app.config import get_settings


async def get_satellite_context(impact_id: str, lat: float, lon: float) -> SatelliteContext:
    """
    Récupère le contexte satellite pour un impact.
    
    Args:
        impact_id: ID de l'impact (ObjectId MongoDB)
        lat: Latitude (utilisé pour le mock)
        lon: Longitude (utilisé pour le mock)
    
    Returns:
        SatelliteContext avec URL de tuile et couverture nuageuse
    """
    settings = get_settings()
    
    if settings.use_mock_satellite:
        return _mock_satellite_context(impact_id, lat, lon)
    else:
        return await _fetch_satellite_context(impact_id, lat, lon)


async def _fetch_satellite_context(impact_id: str, lat: float, lon: float) -> SatelliteContext:
    """
    Appelle le vrai satellite-service.
    
    Le satellite-service récupérera l'impact via notre API pour obtenir lat/lon.
    """
    settings = get_settings()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{settings.satellite_service_url}/api/satellite/tiles/impacts/{impact_id}"
            )
            response.raise_for_status()
            data = response.json()
            
            return SatelliteContext(
                latitude=lat,
                longitude=lon,
                timestamp=datetime.utcnow(),
                tile_url=data.get("tile_url"),
                cloud_coverage=data.get("cloud_coverage"),
                metadata=data.get("metadata", {})
            )
        except Exception as e:
            # Fallback to mock if satellite-service fails
            print(f"Satellite service error: {e}, using mock")
            return _mock_satellite_context(impact_id, lat, lon)


def _mock_satellite_context(impact_id: str, lat: float, lon: float) -> SatelliteContext:
    """Génère des données satellite simulées."""
    
    return SatelliteContext(
        latitude=lat,
        longitude=lon,
        timestamp=datetime.utcnow(),
        tile_url=f"https://mock-satellite.com/tile/impact/{impact_id}.png",
        cloud_coverage=round(random.uniform(20, 80), 1),
        metadata={"source": "mock", "resolution": "1km", "impact_id": impact_id}
    )
