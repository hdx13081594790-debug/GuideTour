from app.schemas.location import GeoPoint
from app.schemas.navigation import RouteResponse
from app.schemas.poi import POIRead
from app.services.map.base import MapProviderClient
from app.services.map.local_graph_router import LocalGraphRouter

# 高德地图适配器占位。
#
# 目前还没有接真实高德 API，所有路线请求都回退到 LocalGraphRouter。
# 由于它实现了 MapProviderClient，后续补 search_poi/walking_route 时，
# NavigationService 不需要改。


class AmapClient(MapProviderClient):
    name = "amap"

    def __init__(self, key: str | None = None):
        self.key = key
        self.fallback = LocalGraphRouter()

    async def search_poi(self, query: str, location: GeoPoint | None = None, radius: int = 1000) -> list[POIRead]:
        # TODO: 接入高德 POI 搜索。MVP 暂时返回空列表。
        return []

    async def walking_route(self, origin: GeoPoint, destination: GeoPoint, destination_name: str = "目的地") -> RouteResponse:
        return await self.fallback.walking_route(origin, destination, destination_name)

    async def reverse_geocode(self, location: GeoPoint) -> str:
        return await self.fallback.reverse_geocode(location)
