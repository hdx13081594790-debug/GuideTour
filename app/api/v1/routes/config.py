from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

# 配置路由。
#
# 主要给浏览器端读取“安全可公开”的配置，例如地图供应商和浏览器端 AK。
# 服务端密钥如 DEEPSEEK_API_KEY、BAIDU_AK 不应该从这里返回给前端。

router = APIRouter(prefix="/config", tags=["config"])


class MapConfigResponse(BaseModel):
    provider: str
    baidu_browser_ak: str | None = None


@router.get("/map", response_model=MapConfigResponse)
def map_config() -> MapConfigResponse:
    # 前端 initBaiduMap() 调用此接口，拿到 baidu_browser_ak 后再加载百度 JS SDK。
    settings = get_settings()
    return MapConfigResponse(provider=settings.map_provider, baidu_browser_ak=settings.baidu_browser_ak)
