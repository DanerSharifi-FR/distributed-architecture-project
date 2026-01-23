"""
Weather Client
==============
Client pour récupérer les risques météo depuis weather-service.

Le weather-service (PHP/Slim) expose l'API OpenWeather avec cache.
Endpoint: GET /v1/onecall?lat=...&lon=...
"""

import random
import httpx
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
        return await _fetch_weather_risk(lat, lon, alt)


async def _fetch_weather_risk(lat: float, lon: float, alt: float) -> WeatherRisk:
    """
    Appelle le vrai weather-service.
    
    Le weather-service expose /v1/onecall qui proxy OpenWeather.
    On analyse la réponse pour extraire les dangers météo.
    """
    settings = get_settings()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{settings.weather_service_url}/v1/onecall",
                params={"lat": lat, "lon": lon},
                headers={"X-Internal-Token": settings.weather_internal_token}
            )
            response.raise_for_status()
            data = response.json()
            
            # Analyser la réponse OpenWeather pour extraire les risques
            return _parse_weather_response(data, lat, lon, alt)
            
        except Exception as e:
            print(f"⚠️ Weather service error: {e}, using mock")
            return _mock_weather_risk(lat, lon, alt)


def _parse_weather_response(data: dict, lat: float, lon: float, alt: float) -> WeatherRisk:
    """
    Convertit la réponse OpenWeather en WeatherRisk.
    
    Analyse les conditions météo actuelles pour détecter les dangers:
    - Vent fort (> 15 m/s)
    - Orage (weather id 2xx)
    - Visibilité réduite (< 5000m)
    - Pluie/neige intense
    """
    hazards = []
    overall_score = 0.3  # Score de base 
    
    current = data.get("current", {})
    
    # Vérifier la vitesse du vent
    wind_speed = current.get("wind_speed", 0)
    if wind_speed > 15:
        hazards.append(WeatherHazard(
            type="strong_wind",
            severity=min(wind_speed / 30, 1.0),
            description=f"Vent à {wind_speed} m/s"
        ))
        overall_score += 0.2
    
    # Vérifier les conditions météo
    weather_list = current.get("weather", [])
    for weather in weather_list:
        weather_id = weather.get("id", 0)
        
        # Orages (2xx)
        if 200 <= weather_id < 300:
            hazards.append(WeatherHazard(
                type="thunderstorm",
                severity=0.9,
                description=weather.get("description", "Orage")
            ))
            overall_score += 0.3
        
        # Pluie forte (5xx avec id > 502)
        elif weather_id > 502 and weather_id < 600:
            hazards.append(WeatherHazard(
                type="heavy_rain",
                severity=0.6,
                description=weather.get("description", "Pluie forte")
            ))
            overall_score += 0.15
        
        # Neige (6xx)
        elif 600 <= weather_id < 700:
            hazards.append(WeatherHazard(
                type="snow",
                severity=0.5,
                description=weather.get("description", "Neige")
            ))
            overall_score += 0.1
    
    # Vérifier la visibilité
    visibility = current.get("visibility", 10000)
    if visibility < 5000:
        hazards.append(WeatherHazard(
            type="low_visibility",
            severity=1 - (visibility / 5000),
            description=f"Visibilité {visibility}m"
        ))
        overall_score += 0.15
    
    return WeatherRisk(
        latitude=lat,
        longitude=lon,
        altitude=alt,
        timestamp=datetime.utcnow(),
        overall_score=min(overall_score, 1.0),
        hazards=hazards
    )


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