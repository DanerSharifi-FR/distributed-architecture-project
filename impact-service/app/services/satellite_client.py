import random
from datetime import datetime
from typing import Optional
import httpx

from app.config import get_settings
from app.models.impact import SatelliteContext


class SatelliteClient:
    """
    Client pour appeler satellite-service.
    Inclut un mode mock pour dev sans le vrai service.
    """

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.satellite_service_url
        self.use_mock = self.settings.use_mock_satellite

    async def get_satellite_context(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None,
        imagery_type: str = "visible",
    ) -> SatelliteContext:
        """
        Récupère le contexte satellite pour une position donnée.
        
        Args:
            latitude: Latitude en degrés
            longitude: Longitude en degrés
            timestamp: Horodatage (optionnel, défaut = now)
            imagery_type: Type d'imagerie ("visible", "infrared", "water_vapor")
        
        Returns:
            SatelliteContext avec URLs des tuiles et métadonnées
        """
        if self.use_mock:
            return await self._mock_satellite_context(latitude, longitude, timestamp, imagery_type)

        return await self._fetch_satellite_context(latitude, longitude, timestamp, imagery_type)

    async def _fetch_satellite_context(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime],
        imagery_type: str,
    ) -> SatelliteContext:
        """Appel réel au satellite-service - à adapter selon l'API de Thomas"""
        timestamp = timestamp or datetime.utcnow()

        async with httpx.AsyncClient(timeout=10.0) as client:
            # URL à adapter selon l'API que Thomas va créer
            response = await client.get(
                f"{self.base_url}/api/satellite/context",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "time": timestamp.isoformat(),
                    "type": imagery_type,
                },
            )
            response.raise_for_status()
            data = response.json()

            return SatelliteContext(
                latitude=latitude,
                longitude=longitude,
                timestamp=timestamp,
                tile_url=data.get("tile_url"),
                snapshot_url=data.get("snapshot_url"),
                cloud_coverage=data.get("cloud_coverage"),
                imagery_type=imagery_type,
                metadata=data,
            )

    async def _mock_satellite_context(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime],
        imagery_type: str,
    ) -> SatelliteContext:
        """
        Mock réaliste pour le dev.
        Génère des données satellite simulées.
        """
        timestamp = timestamp or datetime.utcnow()

        # Simuler une couverture nuageuse variable
        cloud_coverage = random.uniform(0, 100)

        # Générer des URLs fictives mais réalistes
        zoom = 8
        tile_x = int((longitude + 180) / 360 * (2 ** zoom))
        tile_y = int((1 - (latitude + 90) / 180) * (2 ** zoom))

        tile_url = f"https://tiles.example.com/{imagery_type}/{zoom}/{tile_x}/{tile_y}.png"
        snapshot_url = f"https://snapshots.example.com/{imagery_type}/{latitude:.2f}_{longitude:.2f}_{timestamp.strftime('%Y%m%d%H%M')}.png"

        return SatelliteContext(
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            tile_url=tile_url,
            snapshot_url=snapshot_url,
            cloud_coverage=round(cloud_coverage, 1),
            imagery_type=imagery_type,
            metadata={
                "mock": True,
                "resolution": "1km",
                "satellite": "GOES-16" if longitude < -30 else "Meteosat-11",
                "band": "visible" if imagery_type == "visible" else "IR10.8",
            },
        )


# Singleton pour réutilisation
_satellite_client: Optional[SatelliteClient] = None


def get_satellite_client() -> SatelliteClient:
    global _satellite_client
    if _satellite_client is None:
        _satellite_client = SatelliteClient()
    return _satellite_client
