"""
GraphQL Schema
==============
API GraphQL avec Strawberry.

Strawberry transforme des classes Python en schema GraphQL automatiquement.
"""

from datetime import datetime
from typing import Optional
import strawberry
from bson import ObjectId

from app.models.impact import FlightPosition
from app.services.impact_calculator import calculate_impact
from app.services.flight_client import get_flights
from app.services.satellite_client import trigger_satellite_tile
from app.db.mongodb import get_db


# ============ TYPES GraphQL ============

@strawberry.type
class Impact:
    """Type GraphQL pour un impact."""
    id: str
    flight_id: str
    callsign: Optional[str]
    severity: str
    impact_score: float
    description: str


@strawberry.input
class PositionInput:
    """Input pour calculer un impact."""
    flight_id: str
    latitude: float
    longitude: float
    altitude: float
    callsign: Optional[str] = None


# ============ HELPER ============

def doc_to_impact(doc: dict) -> Impact:
    """Convertit un document MongoDB en type GraphQL."""
    return Impact(
        id=str(doc["_id"]),
        flight_id=doc["flight_id"],
        callsign=doc.get("callsign"),
        severity=doc["severity"],
        impact_score=doc["impact_score"],
        description=doc["description"]
    )


# ============ QUERIES (lecture) ============

@strawberry.type
class Query:
    
    @strawberry.field
    async def impacts(self, limit: int = 50) -> list[Impact]:
        """Liste tous les impacts."""
        cursor = get_db().impact.find().limit(limit)
        return [doc_to_impact(doc) async for doc in cursor]

    @strawberry.field
    async def impact(self, id: str) -> Optional[Impact]:
        """Récupère un impact par ID."""
        doc = await get_db().impact.find_one({"_id": ObjectId(id)})
        if not doc:
            return None
        return doc_to_impact(doc)

    @strawberry.field
    async def stats(self) -> str:
        """Nombre total d'impacts."""
        count = await get_db().impact.count_documents({})
        return f"Total: {count} impacts"


# ============ MUTATIONS (écriture) ============

@strawberry.type
class Mutation:

    @strawberry.mutation
    async def create_impact(self, position: PositionInput) -> Impact:
        """
        Calcule et sauvegarde un impact pour une position.
        
        Flow:
        1. Calcule l'impact météo
        2. Sauvegarde en MongoDB
        3. Déclenche la génération de tuile satellite
        """
        # Créer l'objet position
        pos = FlightPosition(
            flight_id=position.flight_id,
            callsign=position.callsign,
            latitude=position.latitude,
            longitude=position.longitude,
            altitude=position.altitude,
            timestamp=datetime.utcnow()
        )
        
        # Calculer l'impact (sans satellite)
        impact = await calculate_impact(pos)
        
        # Sauvegarder en MongoDB
        impact_id = ObjectId()
        doc = impact.model_dump()
        doc["_id"] = impact_id
        await get_db().impact.insert_one(doc)
        
        # Déclencher satellite (après sauvegarde)
        await trigger_satellite_tile(str(impact_id))
        
        return Impact(
            id=str(impact_id),
            flight_id=impact.flight_id,
            callsign=impact.callsign,
            severity=impact.severity.value,
            impact_score=impact.impact_score,
            description=impact.description
        )

    @strawberry.mutation
    async def analyze_flights(self, limit: int = 10) -> list[Impact]:
        """
        Analyse les vols en temps réel.
        
        Flow pour chaque vol:
        1. Calcule l'impact météo
        2. Sauvegarde en MongoDB
        3. Déclenche la génération de tuile satellite
        """
        flights = await get_flights()
        results = []
        
        for flight in flights[:limit]:
            # Calculer l'impact
            impact = await calculate_impact(flight)
            
            # Sauvegarder en MongoDB
            impact_id = ObjectId()
            doc = impact.model_dump()
            doc["_id"] = impact_id
            await get_db().impact.insert_one(doc)
            
            # Déclencher satellite (après sauvegarde)
            await trigger_satellite_tile(str(impact_id))
            
            results.append(Impact(
                id=str(impact_id),
                flight_id=impact.flight_id,
                callsign=impact.callsign,
                severity=impact.severity.value,
                impact_score=impact.impact_score,
                description=impact.description
            ))
        
        return results


# ============ SCHEMA ============

schema = strawberry.Schema(query=Query, mutation=Mutation)
