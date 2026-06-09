from uuid import uuid4
from app.schemas.location import GeoPoint
from app.schemas.navigation import RouteResponse, RouteStep
from app.schemas.poi import POIRead
from app.services.map.base import MapProviderClient
from app.services.map.coordinate import haversine_meters

# 本地园区路网兜底 Provider。
#
# 当没有高德/百度 Key，或外部地图无法返回景区内部路线时，
# NavigationService 会使用 LocalGraphRouter 返回一条可演示路线。
#
# MVP 没有真实路网图结构，因此这里用“起点-中点-终点”的 mock polyline
# 和三段步行指令模拟园区内路线。后续可以替换为真实 graph shortest path。


class LocalGraphRouter(MapProviderClient):
    name = "local"

    async def search_poi(self, query: str, location: GeoPoint | None = None, radius: int = 1000) -> list[POIRead]:
        # 本地路由器不负责 POI 搜索；POI 搜索由 POIRepository 或外部地图完成。
        return []

    async def walking_route(self, origin: GeoPoint, destination: GeoPoint, destination_name: str = "目的地") -> RouteResponse:
        straight = haversine_meters(origin, destination)
        distance = max(straight * 1.25, 30)
        duration = int(distance / 1.1)
        mid = GeoPoint(lng=(origin.lng + destination.lng) / 2, lat=(origin.lat + destination.lat) / 2)
        steps = [
            RouteStep(index=0, instruction=f"沿当前道路向前步行约{int(distance * 0.45)}米", distance_meters=distance * 0.45, duration_seconds=int(duration * 0.45)),
            RouteStep(index=1, instruction=f"到达路口后按园区指示牌前往{destination_name}", distance_meters=distance * 0.35, duration_seconds=int(duration * 0.35), direction="right", action="turn"),
            RouteStep(index=2, instruction=f"继续前行约{int(distance * 0.2)}米，到达{destination_name}", distance_meters=distance * 0.2, duration_seconds=int(duration * 0.2)),
        ]
        return RouteResponse(
            task_id=f"nav_{uuid4().hex[:10]}",
            destination_name=destination_name,
            distance_meters=round(distance, 1),
            duration_seconds=duration,
            polyline=[origin, mid, destination],
            steps=steps,
            tts_text=f"已为你规划去{destination_name}的步行路线，全程约{int(distance)}米，预计{max(1, round(duration / 60))}分钟。请沿当前道路向前步行。",
        )

    async def reverse_geocode(self, location: GeoPoint) -> str:
        return f"颐和园附近({location.lng:.5f},{location.lat:.5f})"
