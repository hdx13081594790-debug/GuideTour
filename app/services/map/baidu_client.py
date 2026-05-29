from app.schemas.location import GeoPoint
from app.schemas.navigation import RouteResponse
from app.schemas.poi import POIRead
from app.services.map.base import MapProviderClient
from app.services.map.local_graph_router import LocalGraphRouter


class BaiduClient(MapProviderClient):
    name = "baidu"

    def __init__(self, ak: str | None = None):
        self.ak = ak
        self.fallback = LocalGraphRouter()

    async def search_poi(self, query: str, location: GeoPoint | None = None, radius: int = 1000) -> list[POIRead]:
        return []

    async def walking_route(self, origin: GeoPoint, destination: GeoPoint, destination_name: str = "目的地") -> RouteResponse:
        return await self.fallback.walking_route(origin, destination, destination_name)

    async def reverse_geocode(self, location: GeoPoint) -> str:
        return await self.fallback.reverse_geocode(location)
