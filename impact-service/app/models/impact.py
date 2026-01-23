from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class ImpactSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FlightPosition(BaseModel):
    flight_id: str
    callsign: Optional[str] = None
    latitude: float
    longitude: float
    altitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: datetime

class WeatherHazard(BaseModel):
    type: str
    severity: float
    description: Optional[str] = None

class WeatherRisk(BaseModel):
    latitude: float
    longitude: float
    altitude: float
    timestamp: datetime
    overall_score: float = Field(ge=0.0, le=1.0)
    hazards: list[WeatherHazard] = []

class Impact(BaseModel):
    flight_id: str
    callsign: Optional[str] = None
    position: FlightPosition
    weather_risk: Optional[WeatherRisk] = None
    severity: ImpactSeverity
    impact_score: float = Field(ge=0.0, le=100.0)
    description: str
    recommendations: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
