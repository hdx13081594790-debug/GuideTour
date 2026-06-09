import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.navigation_task import NavigationTask
from app.schemas.location import GeoPoint
from app.schemas.navigation import RouteResponse, RouteStep

# NavigationRepository 负责 navigation_task 表的持久化。
#
# 它不规划路线、不判断偏航，只把 NavigationService 已经算好的路线
# 保存到数据库，或从数据库还原成 RouteResponse。


class NavigationRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_route(self, session_id: str, route: RouteResponse, origin: GeoPoint, destination_poi_id: int | None, provider: str = "local") -> NavigationTask:
        # RouteResponse 中的 polyline/steps 是结构化对象；
        # 数据库里用 JSON 字符串保存，便于后续恢复。
        task = NavigationTask(
            task_id=route.task_id,
            user_session_id=session_id,
            origin_longitude=origin.lng,
            origin_latitude=origin.lat,
            destination_poi_id=destination_poi_id,
            destination_name=route.destination_name,
            provider=provider,
            status="navigating",
            route_distance_meters=route.distance_meters,
            route_duration_seconds=route.duration_seconds,
            route_polyline=json.dumps([p.model_dump() for p in route.polyline], ensure_ascii=False),
            route_steps=json.dumps([s.model_dump() for s in route.steps], ensure_ascii=False),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get(self, task_id: str) -> NavigationTask | None:
        return self.db.execute(select(NavigationTask).where(NavigationTask.task_id == task_id)).scalar_one_or_none()

    def active_for_session(self, session_id: str) -> NavigationTask | None:
        # 用 session_id 找当前仍在导航中的最近任务。
        return self.db.execute(
            select(NavigationTask)
            .where(NavigationTask.user_session_id == session_id, NavigationTask.status == "navigating")
            .order_by(NavigationTask.created_at.desc())
        ).scalar_one_or_none()

    def cancel(self, task: NavigationTask) -> NavigationTask:
        task.status = "cancelled"
        self.db.commit()
        self.db.refresh(task)
        return task

    def to_response(self, task: NavigationTask) -> RouteResponse:
        # 把数据库任务恢复成前端可消费的 RouteResponse。
        return RouteResponse(
            task_id=task.task_id,
            destination_name=task.destination_name,
            distance_meters=task.route_distance_meters,
            duration_seconds=task.route_duration_seconds,
            polyline=[GeoPoint(**p) for p in json.loads(task.route_polyline or "[]")],
            steps=[RouteStep(**s) for s in json.loads(task.route_steps or "[]")],
            tts_text=f"已为你规划去{task.destination_name}的步行路线，全程约{int(task.route_distance_meters)}米。",
        )
