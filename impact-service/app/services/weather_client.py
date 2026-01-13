import random
from datetime import datetime
from typing import Optional
from app.config import get_settings
from app.models.impact import WeatherRisk, WeatherHazard

class WeatherClient:
    def __init__(self):
        self.use_mock = get_settings().use_mock_weather

    async def get_weather_risk(self, lat, lon, alt, timestamp=None) -> WeatherRisk:
        timestamp = timestamp or datetime.utcnow()
        score = random.uniform(0.2, 0.8)
        hazards = []
        for h, t in [("thunderstorm", 0.7), ("turbulence", 0.5), ("icing", 0.6)]:
            if random.random() > t:
                hazards.append(WeatherHazard(type=h, severity=random.uniform(0.3, 0.9)))
        if hazards: score = max(score, max(h.severity for h in hazards) * 0.8)
        return WeatherRisk(latitude=lat, longitude=lon, altitude=alt, timestamp=timestamp, overall_score=round(score, 3), hazards=hazards)

_client = None
def get_weather_client():
    global _client
    if not _client: _client = WeatherClient()
    return _client
