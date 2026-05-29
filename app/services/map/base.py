from abc import ABC, abstractmethod
from app.schemas.location import GeoPoint
from app.schemas.navigation import RouteResponse
from app.schemas.poi import POIRead


class MapProviderClient(ABC):
    name = "base"

    @abstractmethod
    async def search_poi(self, query: str, location: GeoPoint | None = None, radius: int = 1000) -> list[POIRead]:
        raise NotImplementedError

    @abstractmethod
    async def walking_route(self, origin: GeoPoint, destination: GeoPoint, destination_name: str = "目的地") -> RouteResponse:
        raise NotImplementedError

    @abstractmethod
    async def reverse_geocode(self, location: GeoPoint) -> str:
        raise NotImplementedError
