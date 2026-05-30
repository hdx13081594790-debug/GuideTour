from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.v1.routes import agent, config, location, navigation, photo, poi, rag, vision, ws
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
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/client", include_in_schema=False)
def mobile_client() -> FileResponse:
    return FileResponse(static_dir / "client" / "index.html")


app.include_router(agent.router, prefix=settings.api_prefix)
app.include_router(config.router, prefix=settings.api_prefix)
app.include_router(location.router, prefix=settings.api_prefix)
app.include_router(navigation.router, prefix=settings.api_prefix)
app.include_router(photo.router, prefix=settings.api_prefix)
app.include_router(poi.router, prefix=settings.api_prefix)
app.include_router(rag.router, prefix=settings.api_prefix)
app.include_router(vision.router, prefix=settings.api_prefix)
app.include_router(ws.router, prefix=settings.api_prefix)
