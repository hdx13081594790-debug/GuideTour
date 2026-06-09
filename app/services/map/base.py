from abc import ABC, abstractmethod
from app.schemas.location import GeoPoint
from app.schemas.navigation import RouteResponse
from app.schemas.poi import POIRead

# 地图 Provider 抽象层。
#
# 上层 NavigationService 只调用这三个方法，不关心底层是：
# - 高德 Web 服务；
# - 百度 Web 服务；
# - 景区本地路网 LocalGraphRouter。
#
# 这样更换地图供应商时，导航业务代码不需要改，只替换 Provider。


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
