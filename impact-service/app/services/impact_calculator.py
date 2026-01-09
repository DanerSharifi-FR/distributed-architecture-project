from datetime import datetime
from typing import Optional

from app.models.impact import (
    Impact,
    ImpactSeverity,
    FlightPosition,
    WeatherRisk,
    SatelliteContext,
)
from app.services.weather_client import WeatherClient, get_weather_client
from app.services.satellite_client import SatelliteClient, get_satellite_client


class ImpactCalculator:
    """
    Cerveau du service : calcule l'impact d'un vol en fonction
    des données météo et satellite.
    """

    # Seuils pour déterminer la sévérité
    SEVERITY_THRESHOLDS = {
        ImpactSeverity.LOW: 25,
        ImpactSeverity.MEDIUM: 50,
        ImpactSeverity.HIGH: 75,
        ImpactSeverity.CRITICAL: 100,
    }

    # Poids des différents facteurs dans le calcul
    WEIGHTS = {
        "weather_score": 0.6,
        "hazard_count": 0.15,
        "max_hazard_severity": 0.15,
        "cloud_coverage": 0.1,
    }

    # Recommandations par type de hazard
    HAZARD_RECOMMENDATIONS = {
        "thunderstorm": [
            "Éviter la zone d'orage",
            "Maintenir une distance de sécurité de 20 NM",
            "Contacter le contrôle pour déviation",
        ],
        "turbulence": [
            "Attacher les ceintures",
            "Réduire la vitesse à la vitesse de turbulence",
            "Considérer un changement d'altitude",
        ],
        "icing": [
            "Activer les systèmes anti-givre",
            "Considérer une descente vers une altitude plus chaude",
            "Surveiller les indications de givrage",
        ],
        "strong_wind": [
            "Ajuster le cap pour compenser la dérive",
            "Vérifier la consommation carburant",
        ],
        "low_visibility": [
            "Préparer l'approche aux instruments",
            "Vérifier les minimas de l'aéroport de destination",
        ],
        "precipitation": [
            "Activer les essuie-glaces et anti-pluie",
            "Surveiller le radar météo",
        ],
    }

    def __init__(
        self,
        weather_client: Optional[WeatherClient] = None,
        satellite_client: Optional[SatelliteClient] = None,
    ):
        self.weather_client = weather_client or get_weather_client()
        self.satellite_client = satellite_client or get_satellite_client()

    async def calculate_impact(self, position: FlightPosition) -> Impact:
        """
        Calcule l'impact pour une position de vol.
        
        Args:
            position: Position du vol (lat, lon, alt, etc.)
        
        Returns:
            Impact calculé avec sévérité, score et recommandations
        """
        # 1. Récupérer les données météo
        weather_risk = await self.weather_client.get_weather_risk(
            latitude=position.latitude,
            longitude=position.longitude,
            altitude=position.altitude,
            timestamp=position.timestamp,
        )

        # 2. Récupérer le contexte satellite
        satellite_context = await self.satellite_client.get_satellite_context(
            latitude=position.latitude,
            longitude=position.longitude,
            timestamp=position.timestamp,
        )

        # 3. Calculer le score d'impact
        impact_score = self._compute_impact_score(weather_risk, satellite_context)

        # 4. Déterminer la sévérité
        severity = self._determine_severity(impact_score)

        # 5. Générer la description
        description = self._generate_description(
            position, weather_risk, satellite_context, severity
        )

        # 6. Générer les recommandations
        recommendations = self._generate_recommendations(weather_risk, severity)

        # 7. Créer et retourner l'Impact
        return Impact(
            flight_id=position.flight_id,
            callsign=position.callsign,
            position=position,
            weather_risk=weather_risk,
            satellite_context=satellite_context,
            severity=severity,
            impact_score=impact_score,
            description=description,
            recommendations=recommendations,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def _compute_impact_score(
        self,
        weather_risk: WeatherRisk,
        satellite_context: SatelliteContext,
    ) -> float:
        """Calcule le score d'impact (0-100) basé sur les données collectées."""
        
        # Score météo (0-100)
        weather_score = weather_risk.overall_score * 100

        # Nombre de hazards (0-100, max à 5 hazards)
        hazard_count_score = min(len(weather_risk.hazards) * 20, 100)

        # Sévérité max des hazards (0-100)
        max_hazard_severity = 0
        if weather_risk.hazards:
            max_hazard_severity = max(h.severity for h in weather_risk.hazards) * 100

        # Couverture nuageuse (0-100)
        cloud_score = satellite_context.cloud_coverage or 0

        # Calcul pondéré
        impact_score = (
            self.WEIGHTS["weather_score"] * weather_score
            + self.WEIGHTS["hazard_count"] * hazard_count_score
            + self.WEIGHTS["max_hazard_severity"] * max_hazard_severity
            + self.WEIGHTS["cloud_coverage"] * cloud_score
        )

        return round(min(impact_score, 100), 2)

    def _determine_severity(self, impact_score: float) -> ImpactSeverity:
        """Détermine la sévérité basée sur le score."""
        if impact_score < self.SEVERITY_THRESHOLDS[ImpactSeverity.LOW]:
            return ImpactSeverity.LOW
        elif impact_score < self.SEVERITY_THRESHOLDS[ImpactSeverity.MEDIUM]:
            return ImpactSeverity.MEDIUM
        elif impact_score < self.SEVERITY_THRESHOLDS[ImpactSeverity.HIGH]:
            return ImpactSeverity.HIGH
        else:
            return ImpactSeverity.CRITICAL

    def _generate_description(
        self,
        position: FlightPosition,
        weather_risk: WeatherRisk,
        satellite_context: SatelliteContext,
        severity: ImpactSeverity,
    ) -> str:
        """Génère une description textuelle de l'impact."""
        
        severity_text = {
            ImpactSeverity.LOW: "faible",
            ImpactSeverity.MEDIUM: "modéré",
            ImpactSeverity.HIGH: "élevé",
            ImpactSeverity.CRITICAL: "critique",
        }

        hazard_names = [h.type for h in weather_risk.hazards]
        hazard_text = ", ".join(hazard_names) if hazard_names else "aucun danger détecté"

        cloud_text = f"{satellite_context.cloud_coverage:.0f}%" if satellite_context.cloud_coverage else "non disponible"

        return (
            f"Vol {position.flight_id} ({position.callsign or 'N/A'}) - "
            f"Impact {severity_text[severity]}. "
            f"Position: {position.latitude:.3f}°, {position.longitude:.3f}° à {position.altitude:.0f}m. "
            f"Risque météo: {weather_risk.overall_score:.0%}. "
            f"Dangers: {hazard_text}. "
            f"Couverture nuageuse: {cloud_text}."
        )

    def _generate_recommendations(
        self,
        weather_risk: WeatherRisk,
        severity: ImpactSeverity,
    ) -> list[str]:
        """Génère des recommandations basées sur les dangers détectés."""
        
        recommendations = []

        # Recommandations générales selon sévérité
        if severity == ImpactSeverity.CRITICAL:
            recommendations.append("⚠️ ALERTE CRITIQUE - Action immédiate requise")
            recommendations.append("Contacter le contrôle aérien immédiatement")
        elif severity == ImpactSeverity.HIGH:
            recommendations.append("⚠️ Vigilance accrue recommandée")

        # Recommandations spécifiques par hazard
        for hazard in weather_risk.hazards:
            if hazard.type in self.HAZARD_RECOMMENDATIONS:
                # Ajouter les recos si sévérité du hazard > 0.5
                if hazard.severity > 0.5:
                    recommendations.extend(self.HAZARD_RECOMMENDATIONS[hazard.type])

        # Dédupliquer
        return list(dict.fromkeys(recommendations))


# Singleton
_calculator: Optional[ImpactCalculator] = None


def get_impact_calculator() -> ImpactCalculator:
    global _calculator
    if _calculator is None:
        _calculator = ImpactCalculator()
    return _calculator