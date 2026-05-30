from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(prefix="/config", tags=["config"])


class MapConfigResponse(BaseModel):
    provider: str
    baidu_browser_ak: str | None = None


@router.get("/map", response_model=MapConfigResponse)
def map_config() -> MapConfigResponse:
    settings = get_settings()
    return MapConfigResponse(provider=settings.map_provider, baidu_browser_ak=settings.baidu_browser_ak)
