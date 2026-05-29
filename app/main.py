from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.routes import agent, location, navigation, photo, poi, rag, vision
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.init_db import init_db
from app.schemas.common import HealthResponse
from scripts.seed_poi import seed


configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_exception_handlers(app)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


app.include_router(agent.router, prefix=settings.api_prefix)
app.include_router(location.router, prefix=settings.api_prefix)
app.include_router(navigation.router, prefix=settings.api_prefix)
app.include_router(photo.router, prefix=settings.api_prefix)
app.include_router(poi.router, prefix=settings.api_prefix)
app.include_router(rag.router, prefix=settings.api_prefix)
app.include_router(vision.router, prefix=settings.api_prefix)
