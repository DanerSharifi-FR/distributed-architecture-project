import random
from datetime import datetime
from typing import Optional
import httpx

from app.config import get_settings
from app.models.impact import WeatherRisk, WeatherHazard


class WeatherClient:
    """
    Client pour appeler weather-service.
    Inclut un mode mock pour dev sans le vrai service.
    """

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.weather_service_url
        self.use_mock = self.settings.use_mock_weather

    async def get_weather_risk(
        self,
        latitude: float,
        longitude: float,
        altitude: float,
        timestamp: Optional[datetime] = None,
    ) -> WeatherRisk:
        """
        Récupère le risque météo pour une position donnée.
        
        Args:
            latitude: Latitude en degrés
            longitude: Longitude en degrés
            altitude: Altitude en mètres
            timestamp: Horodatage (optionnel, défaut = now)
        
        Returns:
            WeatherRisk avec le score et les hazards
        """
        if self.use_mock:
            return await self._mock_weather_risk(latitude, longitude, altitude, timestamp)

        return await self._fetch_weather_risk(latitude, longitude, altitude, timestamp)

    async def _fetch_weather_risk(
        self,
        latitude: float,
        longitude: float,
        altitude: float,
        timestamp: Optional[datetime],
    ) -> WeatherRisk:
        """Appel réel au weather-service - à adapter selon l'API de Daner"""
        timestamp = timestamp or datetime.utcnow()

        async with httpx.AsyncClient(timeout=10.0) as client:
            # URL à adapter selon l'API que Daner va créer
            response = await client.get(
                f"{self.base_url}/api/weather/risk",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "alt": altitude,
                    "time": timestamp.isoformat(),
                },
            )
            response.raise_for_status()
            data = response.json()

            # Parser la réponse - structure à adapter
            hazards = [
                WeatherHazard(
                    type=h.get("type"),
                    severity=h.get("severity", 0.0),
                    description=h.get("description"),
                )
                for h in data.get("hazards", [])
            ]

            return WeatherRisk(
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                timestamp=timestamp,
                overall_score=data.get("overall_score", 0.0),
                hazards=hazards,
                raw_data=data,
            )

    async def _mock_weather_risk(
        self,
        latitude: float,
        longitude: float,
        altitude: float,
        timestamp: Optional[datetime],
    ) -> WeatherRisk:
        """
        Mock réaliste pour le dev.
        Génère des données météo simulées basées sur la position.
        """
        timestamp = timestamp or datetime.utcnow()

        # Simuler des conditions météo variables selon la position
        # Plus d'orages dans certaines zones (simulation)
        lat_factor = abs(latitude) / 90.0
        lon_factor = (longitude + 180) / 360.0

        # Score de risque basé sur des facteurs simulés
        base_risk = random.uniform(0.1, 0.4)
        altitude_risk = min(altitude / 12000, 0.3)  # Plus risqué en altitude
        position_risk = (lat_factor + lon_factor) * 0.2

        overall_score = min(base_risk + altitude_risk + position_risk, 1.0)

        # Générer des hazards simulés
        hazards = []
        hazard_types = [
            ("thunderstorm", "Orage", 0.7),
            ("turbulence", "Turbulence", 0.5),
            ("icing", "Givrage", 0.6),
            ("strong_wind", "Vent fort", 0.4),
            ("low_visibility", "Faible visibilité", 0.3),
            ("precipitation", "Précipitations", 0.35),
        ]

        for hazard_type, desc, threshold in hazard_types:
            if random.random() > threshold:
                severity = random.uniform(0.2, 0.9)
                hazards.append(
                    WeatherHazard(
                        type=hazard_type,
                        severity=severity,
                        description=f"{desc} détecté (mock)",
                    )
                )

        # Recalculer le score si on a des hazards
        if hazards:
            max_hazard = max(h.severity for h in hazards)
            overall_score = max(overall_score, max_hazard * 0.8)

        return WeatherRisk(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            timestamp=timestamp,
            overall_score=round(overall_score, 3),
            hazards=hazards,
            raw_data={"mock": True, "seed": f"{latitude:.2f}_{longitude:.2f}"},
        )


# Singleton pour réutilisation
_weather_client: Optional[WeatherClient] = None


def get_weather_client() -> WeatherClient:
    global _weather_client
    if _weather_client is None:
        _weather_client = WeatherClient()
    return _weather_client
