from datetime import datetime
from app.models.impact import Impact, ImpactSeverity, FlightPosition
from app.services.weather_client import get_weather_client
from app.services.satellite_client import get_satellite_client

class ImpactCalculator:
    def __init__(self):
        self.weather = get_weather_client()
        self.satellite = get_satellite_client()

    async def calculate_impact(self, pos: FlightPosition) -> Impact:
        weather = await self.weather.get_weather_risk(pos.latitude, pos.longitude, pos.altitude)
        satellite = await self.satellite.get_satellite_context(pos.latitude, pos.longitude)
        score = weather.overall_score * 60 + min(len(weather.hazards) * 10, 30) + (satellite.cloud_coverage or 0) * 0.1
        score = min(score, 100)
        sev = ImpactSeverity.LOW if score < 25 else ImpactSeverity.MEDIUM if score < 50 else ImpactSeverity.HIGH if score < 75 else ImpactSeverity.CRITICAL
        hazards = ", ".join(h.type for h in weather.hazards) or "aucun"
        return Impact(flight_id=pos.flight_id, callsign=pos.callsign, position=pos, weather_risk=weather, satellite_context=satellite,
            severity=sev, impact_score=round(score, 2), description=f"Vol {pos.flight_id} - Dangers: {hazards}",
            recommendations=["Vigilance"] if sev in [ImpactSeverity.HIGH, ImpactSeverity.CRITICAL] else [])

_calc = None
def get_impact_calculator():
    global _calc
    if not _calc: _calc = ImpactCalculator()
    return _calc
