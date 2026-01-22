"""
Impact Calculator
=================
Logique métier pour calculer l'impact météo d'un vol.
"""

from app.models.impact import Impact, ImpactSeverity, FlightPosition
from app.services.weather_client import get_weather_risk
from app.services.satellite_client import get_satellite_context


async def calculate_impact(position: FlightPosition, impact_id: str) -> Impact:
    """
    Calcule l'impact météo pour une position de vol.
    
    Args:
        position: Position du vol (lat, lon, altitude, etc.)
        impact_id: ID pré-généré de l'impact (ObjectId MongoDB en string)
    
    Étapes:
    1. Récupère les risques météo (weather-service ou mock)
    2. Récupère le contexte satellite (satellite-service ou mock)
    3. Calcule un score de 0 à 100
    4. Détermine la sévérité (low/medium/high/critical)
    """
    
    # 1. Récupérer les données météo et satellite
    weather = await get_weather_risk(position.latitude, position.longitude, position.altitude)
    satellite = await get_satellite_context(impact_id, position.latitude, position.longitude)
    
    # 2. Calculer le score d'impact (0-100)
    #    - 60% basé sur le score météo global
    #    - 30% basé sur le nombre de dangers (max 3)
    #    - 10% basé sur la couverture nuageuse
    score = (
        weather.overall_score * 60 +                    # Score météo
        min(len(weather.hazards) * 10, 30) +            # Nombre de dangers
        (satellite.cloud_coverage or 0) * 0.1           # Couverture nuageuse
    )
    score = min(score, 100)  # Plafonner à 100
    
    # 3. Déterminer la sévérité
    if score < 25:
        severity = ImpactSeverity.LOW
    elif score < 50:
        severity = ImpactSeverity.MEDIUM
    elif score < 75:
        severity = ImpactSeverity.HIGH
    else:
        severity = ImpactSeverity.CRITICAL
    
    # 4. Créer la description
    hazard_names = ", ".join(h.type for h in weather.hazards) or "aucun"
    description = f"Vol {position.flight_id} - Dangers: {hazard_names}"
    
    # 5. Recommandations
    recommendations = []
    if severity in [ImpactSeverity.HIGH, ImpactSeverity.CRITICAL]:
        recommendations.append("Vigilance requise")
    
    # 6. Retourner l'impact
    return Impact(
        flight_id=position.flight_id,
        callsign=position.callsign,
        position=position,
        weather_risk=weather,
        satellite_context=satellite,
        severity=severity,
        impact_score=round(score, 2),
        description=description,
        recommendations=recommendations
    )
