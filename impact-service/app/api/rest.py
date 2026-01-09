from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from bson import ObjectId

from app.models.impact import Impact, ImpactSeverity, FlightPosition
from app.services.impact_calculator import get_impact_calculator


router = APIRouter(prefix="/api", tags=["impacts"])


# ============ Request/Response Models ============

class FlightPositionRequest(BaseModel):
    flight_id: str
    callsign: Optional[str] = None
    latitude: float
    longitude: float
    altitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: Optional[datetime] = None


class ImpactResponse(BaseModel):
    id: str
    flight_id: str
    callsign: Optional[str]
    latitude: float
    longitude: float
    altitude: float
    severity: str
    impact_score: float
    description: str
    recommendations: list[str]
    weather_score: Optional[float]
    cloud_coverage: Optional[float]
    hazards: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_impacts: int
    by_severity: dict[str, int]
    avg_score: float
    recent_critical: int


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    mongo_connected: bool


# ============ Helpers ============

def impact_to_response(impact: Impact) -> ImpactResponse:
    """Convertit un Impact en réponse REST."""
    hazards = []
    weather_score = None
    if impact.weather_risk:
        weather_score = impact.weather_risk.overall_score
        hazards = [h.type for h in impact.weather_risk.hazards]

    cloud_coverage = None
    if impact.satellite_context:
        cloud_coverage = impact.satellite_context.cloud_coverage

    return ImpactResponse(
        id=str(impact.id),
        flight_id=impact.flight_id,
        callsign=impact.callsign,
        latitude=impact.position.latitude,
        longitude=impact.position.longitude,
        altitude=impact.position.altitude,
        severity=impact.severity.value,
        impact_score=impact.impact_score,
        description=impact.description,
        recommendations=impact.recommendations,
        weather_score=weather_score,
        cloud_coverage=cloud_coverage,
        hazards=hazards,
        created_at=impact.created_at,
    )


# ============ Endpoints ============

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    mongo_ok = True
    try:
        # Tenter une opération simple sur MongoDB
        await Impact.find_one()
    except Exception:
        mongo_ok = False

    return HealthResponse(
        status="healthy" if mongo_ok else "degraded",
        service="impact-service",
        timestamp=datetime.utcnow(),
        mongo_connected=mongo_ok,
    )


@router.post("/impacts", response_model=ImpactResponse, status_code=201)
async def create_impact(position: FlightPositionRequest):
    """
    Calcule et persiste un impact à partir d'une position de vol.
    C'est l'endpoint principal pour recevoir des positions.
    """
    flight_position = FlightPosition(
        flight_id=position.flight_id,
        callsign=position.callsign,
        latitude=position.latitude,
        longitude=position.longitude,
        altitude=position.altitude,
        speed=position.speed,
        heading=position.heading,
        timestamp=position.timestamp or datetime.utcnow(),
    )

    calculator = get_impact_calculator()
    impact = await calculator.calculate_impact(flight_position)
    await impact.insert()

    return impact_to_response(impact)


@router.get("/impacts", response_model=list[ImpactResponse])
async def list_impacts(
    flight_id: Optional[str] = Query(None, description="Filtrer par flight_id"),
    severity: Optional[str] = Query(None, description="Filtrer par sévérité"),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_score: Optional[float] = Query(None, ge=0, le=100),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Liste les impacts avec filtres optionnels."""
    query = {}

    if flight_id:
        query["flight_id"] = flight_id
    if severity:
        query["severity"] = severity
    if min_score is not None:
        query["impact_score"] = {"$gte": min_score}
    if max_score is not None:
        if "impact_score" in query:
            query["impact_score"]["$lte"] = max_score
        else:
            query["impact_score"] = {"$lte": max_score}

    impacts = await Impact.find(query).skip(offset).limit(limit).sort(-Impact.created_at).to_list()
    return [impact_to_response(i) for i in impacts]


@router.get("/impacts/{impact_id}", response_model=ImpactResponse)
async def get_impact(impact_id: str):
    """Récupère un impact par son ID."""
    try:
        impact = await Impact.get(ObjectId(impact_id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid impact ID format")

    if not impact:
        raise HTTPException(status_code=404, detail="Impact not found")

    return impact_to_response(impact)


@router.delete("/impacts/{impact_id}", status_code=204)
async def delete_impact(impact_id: str):
    """Supprime un impact."""
    try:
        impact = await Impact.get(ObjectId(impact_id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid impact ID format")

    if not impact:
        raise HTTPException(status_code=404, detail="Impact not found")

    await impact.delete()


@router.get("/impacts/flight/{flight_id}", response_model=list[ImpactResponse])
async def get_impacts_by_flight(flight_id: str, limit: int = Query(20, ge=1, le=100)):
    """Récupère tous les impacts d'un vol spécifique."""
    impacts = await Impact.find(
        Impact.flight_id == flight_id
    ).sort(-Impact.created_at).limit(limit).to_list()
    return [impact_to_response(i) for i in impacts]


@router.get("/impacts/severity/{severity}", response_model=list[ImpactResponse])
async def get_impacts_by_severity(
    severity: str,
    limit: int = Query(50, ge=1, le=200),
):
    """Récupère les impacts par niveau de sévérité."""
    try:
        sev = ImpactSeverity(severity)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity. Must be one of: {[s.value for s in ImpactSeverity]}",
        )

    impacts = await Impact.find(
        Impact.severity == sev
    ).sort(-Impact.created_at).limit(limit).to_list()
    return [impact_to_response(i) for i in impacts]


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Statistiques globales sur les impacts."""
    all_impacts = await Impact.find_all().to_list()

    if not all_impacts:
        return StatsResponse(
            total_impacts=0,
            by_severity={s.value: 0 for s in ImpactSeverity},
            avg_score=0.0,
            recent_critical=0,
        )

    by_severity = {s.value: 0 for s in ImpactSeverity}
    total_score = 0.0

    for impact in all_impacts:
        by_severity[impact.severity.value] += 1
        total_score += impact.impact_score

    # Critiques des dernières 24h
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_critical = await Impact.find(
        Impact.severity == ImpactSeverity.CRITICAL,
        Impact.created_at >= cutoff,
    ).count()

    return StatsResponse(
        total_impacts=len(all_impacts),
        by_severity=by_severity,
        avg_score=round(total_score / len(all_impacts), 2),
        recent_critical=recent_critical,
    )
