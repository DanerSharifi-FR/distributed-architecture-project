from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from beanie import Document


class ImpactSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FlightPosition(BaseModel):
    """Position d'un vol reçue du flight-service"""
    flight_id: str
    callsign: Optional[str] = None
    latitude: float
    longitude: float
    altitude: float  # en mètres
    speed: Optional[float] = None  # en m/s
    heading: Optional[float] = None  # en degrés
    timestamp: datetime


class WeatherHazard(BaseModel):
    """Un danger météo spécifique"""
    type: str  # "thunderstorm", "icing", "turbulence", "low_visibility", "strong_wind", "precipitation"
    severity: float  # 0.0 à 1.0
    description: Optional[str] = None


class WeatherRisk(BaseModel):
    """Risque météo évalué par weather-service"""
    latitude: float
    longitude: float
    altitude: float
    timestamp: datetime
    overall_score: float = Field(ge=0.0, le=1.0)  # Score global de risque 0-1
    hazards: list[WeatherHazard] = []
    raw_data: Optional[dict] = None  # Données brutes de l'API externe


class SatelliteContext(BaseModel):
    """Contexte satellite fourni par satellite-service"""
    latitude: float
    longitude: float
    timestamp: datetime
    tile_url: Optional[str] = None  # URL de la tuile satellite
    snapshot_url: Optional[str] = None  # URL du snapshot
    cloud_coverage: Optional[float] = None  # % de couverture nuageuse
    imagery_type: str = "visible"  # "visible", "infrared", "water_vapor"
    metadata: Optional[dict] = None


class Impact(Document):
    """Document MongoDB - Impact calculé pour un vol"""
    flight_id: str
    callsign: Optional[str] = None
    
    # Position du vol au moment de l'impact
    position: FlightPosition
    
    # Données météo
    weather_risk: Optional[WeatherRisk] = None
    
    # Données satellite
    satellite_context: Optional[SatelliteContext] = None
    
    # Impact calculé
    severity: ImpactSeverity
    impact_score: float = Field(ge=0.0, le=100.0)  # Score 0-100
    description: str
    recommendations: list[str] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "impacts"
        indexes = [
            "flight_id",
            "severity",
            "created_at",
        ]
