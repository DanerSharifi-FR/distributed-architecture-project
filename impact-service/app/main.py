"""
Impact Service - Main
=====================
Point d'entrée de l'application FastAPI.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from app.db.mongodb import init_db, close_db
from app.api.rest import router as rest_router
from app.schemas.graphql import schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application.
    
    - Au démarrage: connecte MongoDB
    - À l'arrêt: déconnecte MongoDB
    """
    await init_db()
    yield
    await close_db()


# Créer l'application
app = FastAPI(
    title="Impact Service",
    description="Calcul d'impact météo pour les vols",
    version="1.0.0",
    lifespan=lifespan
)

# Ajouter les routes REST (/api/*)
app.include_router(rest_router)

# Ajouter GraphQL (/graphql)
app.include_router(GraphQLRouter(schema), prefix="/graphql")
