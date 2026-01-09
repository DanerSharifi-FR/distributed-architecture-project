from datetime import datetime
from enum import Enum
from typing import Optional
import strawberry

from app.models.impact import Impact, ImpactSeverity as ImpactSeverityEnum


# ============ Types GraphQL ============

@strawberry.enum
class ImpactSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@strawberry.type
class FlightPositionType:
    flight_id: str
    callsign: Optional[str]
    latitude: float
    longitude: float
    altitude: float
    speed: Optional[float]
    heading: Optional[float]
    timestamp: datetime


@strawberry.type
class WeatherHazardType:
    type: str
    severity: float
    description: Optional[str]


@strawberry.type
class WeatherRiskType:
    latitude: float
    longitude: float
    altitude: float
    timestamp: datetime
    overall_score: float
    hazards: list[WeatherHazardType]


@strawberry.type
class SatelliteContextType:
    latitude: float
    longitude: float
    timestamp: datetime
    tile_url: Optional[str]
    snapshot_url: Optional[str]
    cloud_coverage: Optional[float]
    imagery_type: str


@strawberry.type
class ImpactType:
    id: str
    flight_id: str
    callsign: Optional[str]
    position: FlightPositionType
    weather_risk: Optional[WeatherRiskType]
    satellite_context: Optional[SatelliteContextType]
    severity: str
    impact_score: float
    description: str
    recommendations: list[str]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ImpactStats:
    total_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    avg_impact_score: float


# ============ Input Types ============

@strawberry.input
class FlightPositionInput:
    flight_id: str
    callsign: Optional[str] = None
    latitude: float
    longitude: float
    altitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: Optional[datetime] = None


@strawberry.input
class ImpactFilterInput:
    flight_id: Optional[str] = None
    severity: Optional[str] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


# ============ Helpers ============

def impact_to_graphql(impact: Impact) -> ImpactType:
    """Convertit un Impact MongoDB en ImpactType GraphQL."""
    weather_risk = None
    if impact.weather_risk:
        weather_risk = WeatherRiskType(
            latitude=impact.weather_risk.latitude,
            longitude=impact.weather_risk.longitude,
            altitude=impact.weather_risk.altitude,
            timestamp=impact.weather_risk.timestamp,
            overall_score=impact.weather_risk.overall_score,
            hazards=[
                WeatherHazardType(
                    type=h.type,
                    severity=h.severity,
                    description=h.description,
                )
                for h in impact.weather_risk.hazards
            ],
        )

    satellite_context = None
    if impact.satellite_context:
        satellite_context = SatelliteContextType(
            latitude=impact.satellite_context.latitude,
            longitude=impact.satellite_context.longitude,
            timestamp=impact.satellite_context.timestamp,
            tile_url=impact.satellite_context.tile_url,
            snapshot_url=impact.satellite_context.snapshot_url,
            cloud_coverage=impact.satellite_context.cloud_coverage,
            imagery_type=impact.satellite_context.imagery_type,
        )

    return ImpactType(
        id=str(impact.id),
        flight_id=impact.flight_id,
        callsign=impact.callsign,
        position=FlightPositionType(
            flight_id=impact.position.flight_id,
            callsign=impact.position.callsign,
            latitude=impact.position.latitude,
            longitude=impact.position.longitude,
            altitude=impact.position.altitude,
            speed=impact.position.speed,
            heading=impact.position.heading,
            timestamp=impact.position.timestamp,
        ),
        weather_risk=weather_risk,
        satellite_context=satellite_context,
        severity=impact.severity.value,
        impact_score=impact.impact_score,
        description=impact.description,
        recommendations=impact.recommendations,
        created_at=impact.created_at,
        updated_at=impact.updated_at,
    )


# ============ Queries ============

@strawberry.type
class Query:
    @strawberry.field
    async def impact(self, id: str) -> Optional[ImpactType]:
        """Récupère un impact par son ID."""
        from bson import ObjectId
        
        try:
            impact = await Impact.get(ObjectId(id))
            if impact:
                return impact_to_graphql(impact)
        except Exception:
            pass
        return None

    @strawberry.field
    async def impacts(
        self,
        filter: Optional[ImpactFilterInput] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ImpactType]:
        """Récupère les impacts avec filtres optionnels."""
        
        query = {}
        
        if filter:
            if filter.flight_id:
                query["flight_id"] = filter.flight_id
            if filter.severity:
                query["severity"] = filter.severity
            if filter.min_score is not None:
                query["impact_score"] = {"$gte": filter.min_score}
            if filter.max_score is not None:
                if "impact_score" in query:
                    query["impact_score"]["$lte"] = filter.max_score
                else:
                    query["impact_score"] = {"$lte": filter.max_score}
            if filter.from_date:
                query["created_at"] = {"$gte": filter.from_date}
            if filter.to_date:
                if "created_at" in query:
                    query["created_at"]["$lte"] = filter.to_date
                else:
                    query["created_at"] = {"$lte": filter.to_date}

        impacts = await Impact.find(query).skip(offset).limit(limit).to_list()
        return [impact_to_graphql(i) for i in impacts]

    @strawberry.field
    async def impacts_by_flight(self, flight_id: str, limit: int = 20) -> list[ImpactType]:
        """Récupère tous les impacts d'un vol spécifique."""
        impacts = await Impact.find(
            Impact.flight_id == flight_id
        ).sort(-Impact.created_at).limit(limit).to_list()
        return [impact_to_graphql(i) for i in impacts]

    @strawberry.field
    async def critical_impacts(self, limit: int = 20) -> list[ImpactType]:
        """Récupère les impacts critiques récents."""
        impacts = await Impact.find(
            Impact.severity == ImpactSeverityEnum.CRITICAL
        ).sort(-Impact.created_at).limit(limit).to_list()
        return [impact_to_graphql(i) for i in impacts]

    @strawberry.field
    async def impact_stats(self) -> ImpactStats:
        """Statistiques globales sur les impacts."""
        all_impacts = await Impact.find_all().to_list()
        
        if not all_impacts:
            return ImpactStats(
                total_count=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                avg_impact_score=0.0,
            )

        severity_counts = {
            ImpactSeverityEnum.CRITICAL: 0,
            ImpactSeverityEnum.HIGH: 0,
            ImpactSeverityEnum.MEDIUM: 0,
            ImpactSeverityEnum.LOW: 0,
        }
        
        total_score = 0.0
        for impact in all_impacts:
            severity_counts[impact.severity] += 1
            total_score += impact.impact_score

        return ImpactStats(
            total_count=len(all_impacts),
            critical_count=severity_counts[ImpactSeverityEnum.CRITICAL],
            high_count=severity_counts[ImpactSeverityEnum.HIGH],
            medium_count=severity_counts[ImpactSeverityEnum.MEDIUM],
            low_count=severity_counts[ImpactSeverityEnum.LOW],
            avg_impact_score=round(total_score / len(all_impacts), 2),
        )


# ============ Mutations ============

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def calculate_impact(self, position: FlightPositionInput) -> ImpactType:
        """
        Calcule et persiste l'impact pour une position de vol.
        C'est la mutation principale utilisée quand on reçoit une position.
        """
        from app.models.impact import FlightPosition
        from app.services.impact_calculator import get_impact_calculator

        # Convertir l'input en FlightPosition
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

        # Calculer l'impact
        calculator = get_impact_calculator()
        impact = await calculator.calculate_impact(flight_position)

        # Sauvegarder en MongoDB
        await impact.insert()

        return impact_to_graphql(impact)

    @strawberry.mutation
    async def delete_impact(self, id: str) -> bool:
        """Supprime un impact par son ID."""
        from bson import ObjectId
        
        try:
            impact = await Impact.get(ObjectId(id))
            if impact:
                await impact.delete()
                return True
        except Exception:
            pass
        return False

    @strawberry.mutation
    async def delete_old_impacts(self, before: datetime) -> int:
        """Supprime les impacts avant une certaine date. Retourne le nombre supprimé."""
        result = await Impact.find(Impact.created_at < before).delete()
        return result.deleted_count if result else 0


# ============ Schema ============

schema = strawberry.Schema(query=Query, mutation=Mutation)
