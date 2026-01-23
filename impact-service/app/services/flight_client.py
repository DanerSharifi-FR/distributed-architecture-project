"""
Flight Client
=============
Client pour récupérer les vols depuis flight-service.
"""

from datetime import datetime
import httpx
from app.models.impact import FlightPosition
from app.config import get_settings


async def get_flights(
    lamin: float = None,
    lomin: float = None, 
    lamax: float = None,
    lomax: float = None
) -> list[FlightPosition]:
    """
    Récupère les vols actuels depuis flight-service.
    
    Args:
        lamin, lomin, lamax, lomax: Bounding box optionnelle
    
    Returns:
        Liste de positions de vol
    """
    settings = get_settings()
    url = f"{settings.flight_service_url}/flights"
    
    # Ajouter les paramètres de bounding box si fournis
    params = {}
    if lamin: params["lamin"] = lamin
    if lomin: params["lomin"] = lomin
    if lamax: params["lamax"] = lamax
    if lomax: params["lomax"] = lomax
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        # Convertir en FlightPosition
        # Le flight-service retourne un array directement
        flights = []
        for f in data:
            # Skip flights with missing position data
            if not f.get("lat") or not f.get("lon"):
                continue
                
            flights.append(FlightPosition(
                flight_id=f.get("icao24", "unknown"),
                callsign=f.get("callsign"),
                latitude=f.get("lat", 0),
                longitude=f.get("lon", 0),
                altitude=f.get("baro_altitude_m", 0) or 0,
                speed=f.get("velocity_mps"),
                heading=f.get("true_track_deg"),
                timestamp=datetime.utcnow()
            ))
        
        return flights
        
    except Exception as e:
        print(f"⚠️ Erreur flight-service: {e}")
        return []
