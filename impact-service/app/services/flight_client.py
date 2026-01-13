from datetime import datetime
from typing import Optional
import httpx
from app.config import get_settings
from app.models.impact import FlightPosition

class FlightClient:
    def __init__(self):
        self.base_url = get_settings().flight_service_url

    async def get_flights(self, lamin=None, lomin=None, lamax=None, lomax=None) -> list[FlightPosition]:
        params = {}
        if all(v is not None for v in [lamin, lomin, lamax, lomax]):
            params = {"lamin": lamin, "lomin": lomin, "lamax": lamax, "lomax": lomax}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/flights", params=params)
            response.raise_for_status()
            return [FlightPosition(
                flight_id=f["icao24"], callsign=f.get("callsign"),
                latitude=f["lat"], longitude=f["lon"],
                altitude=f.get("baro_altitude_m") or f.get("geo_altitude_m") or 0,
                speed=f.get("velocity_mps"), heading=f.get("true_track_deg"),
                timestamp=datetime.utcnow()
            ) for f in response.json()]

_client = None
def get_flight_client():
    global _client
    if not _client: _client = FlightClient()
    return _client
