from sqlalchemy.orm import Session
from app.core.exceptions import AppError
from app.core.config import get_settings
from app.repositories.navigation_repo import NavigationRepository
from app.repositories.poi_repo import POIRepository
from app.schemas.location import GeoPoint
from app.schemas.navigation import NavigationUpdateResponse, RouteRequest, RouteResponse
from app.services.map.amap_client import AmapClient
from app.services.map.baidu_client import BaiduClient
from app.services.map.coordinate import haversine_meters
from app.services.map.local_graph_router import LocalGraphRouter


class NavigationService:
    def __init__(self, db: Session):
        self.db = db
        self.poi_repo = POIRepository(db)
        self.nav_repo = NavigationRepository(db)
        settings = get_settings()
        self.provider = {"amap": AmapClient(settings.amap_key), "baidu": BaiduClient(settings.baidu_ak)}.get(settings.map_provider, LocalGraphRouter())

    async def plan_route(self, request: RouteRequest) -> RouteResponse:
        poi = None
        if request.destination.poi_id:
            poi = self.poi_repo.get(request.destination.poi_id)
        elif request.destination.name:
            matches = self.poi_repo.search(query=request.destination.name, limit=1)
            poi = matches[0] if matches else None
        if not poi:
            raise AppError("没有找到目的地 POI", 404)
        destination = GeoPoint(lng=poi.longitude, lat=poi.latitude)
        route = await self.provider.walking_route(request.origin, destination, poi.name)
        self.nav_repo.save_route(request.session_id, route, request.origin, poi.id, provider=self.provider.name)
        return route

    async def nearest_route(self, session_id: str, origin: GeoPoint, target_type: str, radius_meters: float = 1000) -> RouteResponse:
        candidates = self.poi_repo.nearby(origin, poi_type=target_type, radius_meters=radius_meters)[:3]
        if not candidates:
            raise AppError(f"附近没有找到 {target_type}", 404)
        best: RouteResponse | None = None
        best_poi_id: int | None = None
        for poi, _ in candidates:
            route = await self.provider.walking_route(origin, GeoPoint(lng=poi.longitude, lat=poi.latitude), poi.name)
            if best is None or route.distance_meters < best.distance_meters:
                best, best_poi_id = route, poi.id
        assert best is not None
        self.nav_repo.save_route(session_id, best, origin, best_poi_id, provider=self.provider.name)
        return best

    def update_position(self, task_id: str, location: GeoPoint) -> NavigationUpdateResponse:
        task = self.nav_repo.get(task_id)
        if not task:
            raise AppError("导航任务不存在", 404)
        destination = GeoPoint(lng=0, lat=0)
        poi = self.poi_repo.get(task.destination_poi_id) if task.destination_poi_id else None
        if poi:
            destination = GeoPoint(lng=poi.longitude, lat=poi.latitude)
        remaining = haversine_meters(location, destination) if poi else max(task.route_distance_meters, 0)
        instruction = "你已接近目的地" if remaining < 25 else f"继续前行，距离{task.destination_name}约{int(remaining)}米"
        return NavigationUpdateResponse(
            status="arrived" if remaining < 25 else task.status,
            current_step_index=task.current_step_index,
            instruction=instruction,
            distance_to_next_step_meters=min(30, remaining),
            distance_to_destination_meters=round(remaining, 1),
            off_route=False,
            tts_text=instruction,
        )

    def stop(self, session_id: str, task_id: str | None = None) -> str:
        task = self.nav_repo.get(task_id) if task_id else self.nav_repo.active_for_session(session_id)
        if not task:
            raise AppError("没有正在进行的导航任务", 404)
        self.nav_repo.cancel(task)
        return task.task_id
