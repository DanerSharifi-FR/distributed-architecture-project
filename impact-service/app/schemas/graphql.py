from datetime import datetime
from typing import Optional
import strawberry
from bson import ObjectId
from app.models.impact import Impact as ImpactModel, ImpactSeverity as ImpactSev, FlightPosition
from app.services import get_impact_calculator, get_flight_client

@strawberry.enum
class ImpactSeverity:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@strawberry.type
class ImpactType:
    id: str
    flight_id: str
    callsign: Optional[str]
    severity: str
    impact_score: float
    description: str

@strawberry.input
class FlightPositionInput:
    flight_id: str
    latitude: float
    longitude: float
    altitude: float
    callsign: Optional[str] = None

@strawberry.type
class Query:
    @strawberry.field
    async def impact(self, id: str) -> Optional[ImpactType]:
        i = await ImpactModel.get(ObjectId(id))
        if not i: return None
        return ImpactType(id=str(i.id), flight_id=i.flight_id, callsign=i.callsign, severity=i.severity.value, impact_score=i.impact_score, description=i.description)

    @strawberry.field
    async def impacts(self, limit: int = 50) -> list[ImpactType]:
        return [ImpactType(id=str(i.id), flight_id=i.flight_id, callsign=i.callsign, severity=i.severity.value, impact_score=i.impact_score, description=i.description) for i in await ImpactModel.find_all().limit(limit).to_list()]

    @strawberry.field
    async def stats(self) -> str:
        all = await ImpactModel.find_all().to_list()
        return f"Total: {len(all)} impacts"

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def calculate_impact(self, position: FlightPositionInput) -> ImpactType:
        pos = FlightPosition(flight_id=position.flight_id, callsign=position.callsign, latitude=position.latitude, longitude=position.longitude, altitude=position.altitude, timestamp=datetime.utcnow())
        impact = await get_impact_calculator().calculate_impact(pos)
        await impact.insert()
        return ImpactType(id=str(impact.id), flight_id=impact.flight_id, callsign=impact.callsign, severity=impact.severity.value, impact_score=impact.impact_score, description=impact.description)

    @strawberry.mutation
    async def analyze_flights_from_service(self, limit: int = 10) -> list[ImpactType]:
        flights = await get_flight_client().get_flights()
        calc = get_impact_calculator()
        results = []
        for f in flights[:limit]:
            impact = await calc.calculate_impact(f)
            await impact.insert()
            results.append(ImpactType(id=str(impact.id), flight_id=impact.flight_id, callsign=impact.callsign, severity=impact.severity.value, impact_score=impact.impact_score, description=impact.description))
        return results

schema = strawberry.Schema(query=Query, mutation=Mutation)
