from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from bson import ObjectId
from app.models.impact import Impact, ImpactSeverity, FlightPosition
from app.services import get_impact_calculator, get_flight_client

router = APIRouter(prefix="/api", tags=["impacts"])

class PositionReq(BaseModel):
    flight_id: str
    latitude: float
    longitude: float
    altitude: float
    callsign: Optional[str] = None

class ImpactRes(BaseModel):
    id: str
    flight_id: str
    callsign: Optional[str]
    severity: str
    impact_score: float
    description: str
    class Config:
        from_attributes = True

@router.get("/health")
async def health():
    try: await Impact.find_one()
    except: return {"status": "degraded", "mongo": False}
    return {"status": "healthy", "service": "impact-service", "mongo": True}

@router.post("/impacts", response_model=ImpactRes, status_code=201)
async def create_impact(req: PositionReq):
    pos = FlightPosition(flight_id=req.flight_id, callsign=req.callsign, latitude=req.latitude, longitude=req.longitude, altitude=req.altitude, timestamp=datetime.utcnow())
    impact = await get_impact_calculator().calculate_impact(pos)
    await impact.insert()
    return ImpactRes(id=str(impact.id), flight_id=impact.flight_id, callsign=impact.callsign, severity=impact.severity.value, impact_score=impact.impact_score, description=impact.description)

@router.get("/impacts")
async def list_impacts(limit: int = 50):
    return [{"id": str(i.id), "flight_id": i.flight_id, "severity": i.severity.value, "score": i.impact_score} for i in await Impact.find_all().limit(limit).to_list()]

@router.post("/analyze-flights")
async def analyze_flights(lamin: Optional[float] = None, lomin: Optional[float] = None, lamax: Optional[float] = None, lomax: Optional[float] = None, limit: int = 10):
    flights = await get_flight_client().get_flights(lamin, lomin, lamax, lomax)
    calc = get_impact_calculator()
    results = []
    for f in flights[:limit]:
        impact = await calc.calculate_impact(f)
        await impact.insert()
        results.append({"flight_id": impact.flight_id, "callsign": impact.callsign, "severity": impact.severity.value, "impact_score": impact.impact_score})
    return results

@router.get("/stats")
async def stats():
    impacts = await Impact.find_all().to_list()
    by_sev = {s.value: sum(1 for i in impacts if i.severity == s) for s in ImpactSeverity}
    return {"total": len(impacts), "by_severity": by_sev}
