from contextlib import asynccontextmanager
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from app.db import init_db, close_db
from app.api import router as rest_router
from app.schemas import schema

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()

app = FastAPI(title="Impact Service", description="Calcul d'impact meteo pour les vols", version="1.0.0", lifespan=lifespan)
app.include_router(rest_router)
app.include_router(GraphQLRouter(schema), prefix="/graphql")
