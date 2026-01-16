"""
Satellite Client
================
Client pour récupérer le contexte satellite.

Actuellement en MODE MOCK car satellite-service n'est pas encore prêt.
"""

import random
from datetime import datetime
from app.models.impact import SatelliteContext
from app.config import get_settings


async def get_satellite_context(lat: float, lon: float) -> SatelliteContext:
    """
    Récupère le contexte satellite pour une position.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        SatelliteContext avec URL de tuile et couverture nuageuse
    """
    settings = get_settings()
    
    if settings.use_mock_satellite:
        return _mock_satellite_context(lat, lon)
    else:
        # TODO: Appeler le vrai satellite-service quand il sera prêt
        # return await _fetch_satellite_context(lat, lon)
        return _mock_satellite_context(lat, lon)


def _mock_satellite_context(lat: float, lon: float) -> SatelliteContext:
    """Génère des données satellite simulées."""
    
    return SatelliteContext(
        latitude=lat,
        longitude=lon,
        timestamp=datetime.utcnow(),
        tile_url=f"https://mock-satellite.com/tile/{lat}/{lon}.png",
        cloud_coverage=round(random.uniform(20, 80), 1),
        metadata={"source": "mock", "resolution": "1km"}
    )
