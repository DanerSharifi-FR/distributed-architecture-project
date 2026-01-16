"""
Weather Client
==============
Client pour récupérer les risques météo.

Actuellement en MODE MOCK car weather-service n'est pas encore prêt.
"""

import random
from datetime import datetime
from app.models.impact import WeatherRisk, WeatherHazard
from app.config import get_settings


async def get_weather_risk(lat: float, lon: float, alt: float) -> WeatherRisk:
    """
    Récupère les risques météo pour une position.
    
    Args:
        lat: Latitude
        lon: Longitude  
        alt: Altitude en pieds
    
    Returns:
        WeatherRisk avec score global et liste de dangers
    """
    settings = get_settings()
    
    if settings.use_mock_weather:
        return _mock_weather_risk(lat, lon, alt)
    else:
        # TODO: Appeler le vrai weather-service quand il sera prêt
        # return await _fetch_weather_risk(lat, lon, alt)
        return _mock_weather_risk(lat, lon, alt)


def _mock_weather_risk(lat: float, lon: float, alt: float) -> WeatherRisk:
    """Génère des données météo simulées."""
    
    # Types de dangers possibles
    hazard_types = ["thunderstorm", "turbulence", "icing", "wind_shear", "low_visibility"]
    
    # Générer 1-3 dangers aléatoires
    num_hazards = random.randint(1, 3)
    hazards = [
        WeatherHazard(
            type=random.choice(hazard_types),
            severity=round(random.uniform(0.3, 0.9), 2),
            description=f"Détecté à {alt}ft"
        )
        for _ in range(num_hazards)
    ]
    
    return WeatherRisk(
        latitude=lat,
        longitude=lon,
        altitude=alt,
        timestamp=datetime.utcnow(),
        overall_score=round(random.uniform(0.5, 1.0), 2),
        hazards=hazards
    )
