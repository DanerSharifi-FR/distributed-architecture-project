"""
Impact Calculator
=================
Logique métier pour calculer l'impact météo d'un vol.

Note: Le satellite-service est appelé APRÈS la création de l'impact,
pas dans ce module. Voir rest.py et graphql.py.
"""

from app.models.impact import Impact, ImpactSeverity, FlightPosition
from app.services.weather_client import get_weather_risk


async def calculate_impact(position: FlightPosition) -> Impact:
    """
    Calcule l'impact météo pour une position de vol.
    
    Args:
        position: Position du vol (lat, lon, altitude, etc.)
    
    Étapes:
    1. Récupère les risques météo (weather-service ou mock)
    2. Calcule un score de 0 à 100
    3. Détermine la sévérité (low/medium/high/critical)
    
    Note: Le satellite-service est appelé séparément APRÈS
    avoir sauvegardé l'impact en base (voir rest.py).
    """
    
    # 1. Récupérer les données météo
    weather = await get_weather_risk(position.latitude, position.longitude, position.altitude)
    
    # 2. Calculer le score d'impact (0-100)
    #    - 70% basé sur le score météo global
    #    - 30% basé sur le nombre de dangers (max 3)
    score = (
        weather.overall_score * 70 +                    # Score météo
        min(len(weather.hazards) * 10, 30)              # Nombre de dangers
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
        severity=severity,
        impact_score=round(score, 2),
        description=description,
        recommendations=recommendations
    )
