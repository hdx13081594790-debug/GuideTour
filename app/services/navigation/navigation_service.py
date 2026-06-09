import json
import time

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.repositories.navigation_repo import NavigationRepository
from app.repositories.poi_repo import POIRepository
from app.schemas.location import GeoPoint
from app.schemas.navigation import NavigationState, NavigationUpdateResponse, RouteRequest, RouteResponse, RouteStep
from app.schemas.poi import POIRead
from app.services.map.amap_client import AmapClient
from app.services.map.baidu_client import BaiduClient
from app.services.map.base import MapProviderClient
from app.services.map.coordinate import distance_to_polyline_meters, haversine_meters
from app.services.map.local_graph_router import LocalGraphRouter
from app.services.navigation.state_store import navigation_state_store

ARRIVAL_THRESHOLD_METERS = 25
STEP_ADVANCE_THRESHOLD_METERS = 20
OFF_ROUTE_THRESHOLD_METERS = 30
OFF_ROUTE_CONFIRM_COUNT = 3

# NavigationService 是导航业务的核心层。
# 它把“用户要去哪里”转换为“路线任务 + 实时导航状态”：
#
# 输入：
# - RouteRequest：明确目的地；
# - NearestRequest：最近厕所/出口等服务点；
# - NavigationUpdateRequest：导航中周期性上传当前位置。
#
# 输出：
# - RouteResponse：初始路线、polyline、steps、TTS；
# - NavigationUpdateResponse：当前 step、剩余距离、是否偏航、下一句提示。
#
# 状态流向：
# 1. 路线任务长期保存到 MySQL/SQLite 的 navigation_task；
# 2. 导航实时状态保存到 RedisNavigationStateStore；
# 3. 路由层再把状态通过 WebSocket 推给前端。


def get_map_provider() -> MapProviderClient:
    # 地图 Provider 策略入口。业务层只依赖 MapProviderClient 抽象，
    # 不直接写死高德/百度/本地路网。
    settings = get_settings()
    return {
        "amap": AmapClient(settings.amap_key),
        "baidu": BaiduClient(settings.baidu_ak),
    }.get(settings.map_provider, LocalGraphRouter())


class NavigationService:
    def __init__(self, db: Session):
        self.db = db
        self.poi_repo = POIRepository(db)
        self.nav_repo = NavigationRepository(db)
        self.provider = get_map_provider()

    async def plan_route(self, request: RouteRequest) -> RouteResponse:
        # 指定目的地路线规划：
        # 1. 优先用本地 POI 表解析 poi_id/name；
        # 2. 本地查不到时，调用地图 Provider 的 POI 搜索；
        # 3. 拿到目的地坐标后调用 walking_route；
        # 4. 保存数据库任务和 Redis 实时状态。
        poi = None
        external_poi = None
        if request.destination.poi_id:
            poi = self.poi_repo.get(request.destination.poi_id)
        elif request.destination.name:
            matches = self.poi_repo.search(query=request.destination.name, limit=1)
            poi = matches[0] if matches else None
            if not poi:
                external_matches = await self.provider.search_poi(request.destination.name, request.origin, radius=3000)
                external_poi = external_matches[0] if external_matches else None
        if not poi and not external_poi:
            raise AppError("没有找到目的地 POI", 404)

        destination_name = poi.name if poi else external_poi.name
        destination = GeoPoint(lng=poi.longitude, lat=poi.latitude) if poi else external_poi.location
        destination_poi_id = poi.id if poi else None
        route = await self.provider.walking_route(request.origin, destination, destination_name)
        self.nav_repo.save_route(request.session_id, route, request.origin, destination_poi_id, provider=self.provider.name)
        self._save_started_state(request.session_id, route, destination_poi_id)
        return route

    async def nearest_route(self, session_id: str, origin: GeoPoint, target_type: str, radius_meters: float = 1000) -> RouteResponse:
        # 最近服务点路线：
        # 先按直线距离找最近 3 个本地候选，再逐个规划步行路线，
        # 最终选择“步行距离最短”的路线，而不是单纯直线最近。
        candidates = self.poi_repo.nearby(origin, poi_type=target_type, radius_meters=radius_meters)[:3]
        if not candidates:
            external = await self.provider.search_poi(target_type, origin, radius=int(radius_meters))
            if external:
                return await self._route_to_external_poi(session_id, origin, external[0])
            raise AppError(f"附近没有找到 {target_type}", 404)
        best: RouteResponse | None = None
        best_poi_id: int | None = None
        for poi, _ in candidates:
            route = await self.provider.walking_route(origin, GeoPoint(lng=poi.longitude, lat=poi.latitude), poi.name)
            if best is None or route.distance_meters < best.distance_meters:
                best, best_poi_id = route, poi.id
        assert best is not None
        self.nav_repo.save_route(session_id, best, origin, best_poi_id, provider=self.provider.name)
        self._save_started_state(session_id, best, best_poi_id)
        return best

    async def _route_to_external_poi(self, session_id: str, origin: GeoPoint, poi: POIRead) -> RouteResponse:
        route = await self.provider.walking_route(origin, poi.location, poi.name)
        self.nav_repo.save_route(session_id, route, origin, None, provider=self.provider.name)
        self._save_started_state(session_id, route, None)
        return route

    def update_position(self, task_id: str, location: GeoPoint) -> NavigationUpdateResponse:
        # 导航中位置更新：
        # - 从数据库和 Redis 还原当前任务状态；
        # - 计算当前位置到终点的距离；
        # - 计算当前位置到路线 polyline 的最短距离；
        # - 判断是否推进 step、是否到达、是否连续偏航；
        # - 把新状态写回数据库/Redis，并返回下一句导航提示。
        task = self.nav_repo.get(task_id)
        if not task:
            raise AppError("导航任务不存在", 404)
        state = self._state_from_task(task)
        steps = self._steps_from_task(task)
        destination = self._destination_for_task(task.destination_poi_id) or self._destination_from_state(state)
        distance_to_destination = haversine_meters(location, destination) if destination else max(state.route_distance_meters, 0)
        distance_to_route = distance_to_polyline_meters(location, state.route_polyline)
        off_route = distance_to_route > OFF_ROUTE_THRESHOLD_METERS
        # 定位会抖动，所以不是一次超出阈值就判定偏航。
        # 连续 OFF_ROUTE_CONFIRM_COUNT 次都离路线太远，才确认偏航。
        off_route_count = state.off_route_count + 1 if off_route else 0

        current_step_index = self._advanced_step_index(state.current_step_index, steps, distance_to_destination)
        distance_to_next_step = self._distance_to_next_step(steps, current_step_index, distance_to_destination)

        status = "arrived" if distance_to_destination <= ARRIVAL_THRESHOLD_METERS else "navigating"
        confirmed_off_route = off_route_count >= OFF_ROUTE_CONFIRM_COUNT and status != "arrived"
        instruction = self._instruction(status, confirmed_off_route, steps, current_step_index, distance_to_next_step, task.destination_name)

        task.current_step_index = current_step_index
        task.status = status
        self.db.commit()

        state.status = status
        state.current_step_index = current_step_index
        state.distance_to_next_step_meters = round(distance_to_next_step, 1)
        state.distance_to_destination_meters = round(distance_to_destination, 1)
        state.off_route = confirmed_off_route
        state.off_route_count = off_route_count
        state.last_instruction = instruction
        state.last_location = location
        navigation_state_store.save(state)

        return NavigationUpdateResponse(
            status=status,
            current_step_index=current_step_index,
            instruction=instruction,
            distance_to_next_step_meters=round(distance_to_next_step, 1),
            distance_to_destination_meters=round(distance_to_destination, 1),
            off_route=confirmed_off_route,
            tts_text=instruction,
        )

    def stop(self, session_id: str, task_id: str | None = None) -> str:
        # 停止导航既可以指定 task_id，也可以停止当前 session 的活动任务。
        task = self.nav_repo.get(task_id) if task_id else self.nav_repo.active_for_session(session_id)
        if not task:
            raise AppError("没有正在进行的导航任务", 404)
        self.nav_repo.cancel(task)
        state = self._state_from_task(task)
        state.status = "cancelled"
        state.last_instruction = "已停止导航。"
        navigation_state_store.save(state)
        return task.task_id

    def get_state(self, task_id: str) -> NavigationState | None:
        return navigation_state_store.get(task_id)

    def get_active_state(self, session_id: str) -> NavigationState | None:
        return navigation_state_store.active_for_session(session_id)

    def _save_started_state(self, session_id: str, route: RouteResponse, destination_poi_id: int | None) -> None:
        # 创建导航后立刻写入 Redis 状态，这样前端刷新页面后仍能恢复
        # 当前正在导航的任务。
        first_instruction = route.steps[0].instruction if route.steps else route.tts_text
        navigation_state_store.save(
            NavigationState(
                task_id=route.task_id,
                session_id=session_id,
                status="navigating",
                destination_name=route.destination_name,
                destination_poi_id=destination_poi_id,
                provider=self.provider.name,
                current_step_index=0,
                distance_to_next_step_meters=route.steps[0].distance_meters if route.steps else route.distance_meters,
                distance_to_destination_meters=route.distance_meters,
                off_route=False,
                off_route_count=0,
                last_instruction=first_instruction,
                route_distance_meters=route.distance_meters,
                route_duration_seconds=route.duration_seconds,
                route_polyline=route.polyline,
                updated_at=time.time(),
            )
        )

    def _state_from_task(self, task) -> NavigationState:
        # 优先读 Redis 中的实时状态；如果 Redis 没有，再从数据库任务
        # 重建一个基础状态。这样 Redis 丢失时仍能降级恢复。
        existing = navigation_state_store.get(task.task_id)
        if existing:
            return existing
        return NavigationState(
            task_id=task.task_id,
            session_id=task.user_session_id,
            status=task.status,
            destination_name=task.destination_name,
            destination_poi_id=task.destination_poi_id,
            provider=task.provider,
            current_step_index=task.current_step_index,
            route_distance_meters=task.route_distance_meters,
            route_duration_seconds=task.route_duration_seconds,
            route_polyline=[GeoPoint(**p) for p in json.loads(task.route_polyline or "[]")],
            updated_at=time.time(),
        )

    def _steps_from_task(self, task) -> list[RouteStep]:
        return [RouteStep(**s) for s in json.loads(task.route_steps or "[]")]

    def _destination_for_task(self, destination_poi_id: int | None) -> GeoPoint | None:
        if not destination_poi_id:
            return None
        poi = self.poi_repo.get(destination_poi_id)
        if not poi:
            return None
        return GeoPoint(lng=poi.longitude, lat=poi.latitude)

    def _destination_from_state(self, state: NavigationState) -> GeoPoint | None:
        return state.route_polyline[-1] if state.route_polyline else None

    def _advanced_step_index(self, current_index: int, steps: list[RouteStep], distance_to_destination: float) -> int:
        # step 推进采用“剩余总距离”粗略判断。MVP 阶段没有真实路网点吸附，
        # 所以用距离阈值判断是否已接近下一步。
        if not steps:
            return 0
        remaining = distance_to_destination
        total_from_step = sum(step.distance_meters for step in steps[current_index:])
        index = current_index
        while index < len(steps) - 1 and remaining < max(0, total_from_step - steps[index].distance_meters + STEP_ADVANCE_THRESHOLD_METERS):
            total_from_step -= steps[index].distance_meters
            index += 1
        return index

    def _distance_to_next_step(self, steps: list[RouteStep], current_step_index: int, distance_to_destination: float) -> float:
        if not steps:
            return distance_to_destination
        remaining_after_current = sum(step.distance_meters for step in steps[current_step_index + 1:])
        return max(0, distance_to_destination - remaining_after_current)

    def _instruction(
        self,
        status: str,
        confirmed_off_route: bool,
        steps: list[RouteStep],
        current_step_index: int,
        distance_to_next_step: float,
        destination_name: str,
    ) -> str:
        # 统一生成导航 TTS 文案。前端不自己拼导航句子，只展示后端返回。
        if status == "arrived":
            return f"你已到达{destination_name}附近。"
        if confirmed_off_route:
            return "你似乎偏离了路线，我正在重新规划。"
        if not steps:
            return f"继续前行，距离{destination_name}约{int(distance_to_next_step)}米。"
        step = steps[min(current_step_index, len(steps) - 1)]
        if distance_to_next_step <= STEP_ADVANCE_THRESHOLD_METERS and current_step_index < len(steps) - 1:
            return steps[current_step_index + 1].instruction
        return f"前方约{int(distance_to_next_step)}米，{step.instruction}"
