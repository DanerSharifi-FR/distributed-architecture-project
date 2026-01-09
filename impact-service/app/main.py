from contextlib import asynccontextmanager
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from app.config import get_settings
from app.db import init_db, close_db
from app.api import router as rest_router
from app.schemas import schema

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Démarrage et arrêt de l'app."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="Service de calcul d'impact météo pour les vols",
    version="1.0.0",
    lifespan=lifespan,
)

# REST API
app.include_router(rest_router)

# GraphQL
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "endpoints": {
            "rest": "/api",
            "graphql": "/graphql",
            "docs": "/docs",
        },
    }
