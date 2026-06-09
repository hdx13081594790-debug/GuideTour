from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.location import GeoPoint

# 导航相关的数据契约。
#
# 数据流：
# 前端/Agent 发送 RouteRequest 或 NearestRequest；
# NavigationService 返回 RouteResponse；
# 导航过程中 update-position 返回 NavigationUpdateResponse；
# Redis 中保存 NavigationState，供 WebSocket 和刷新恢复使用。


class DestinationRef(BaseModel):
    # 目的地可以通过本地 poi_id 指定，也可以通过名称让后端搜索。
    poi_id: int | None = None
    name: str | None = None


class RouteStep(BaseModel):
    # 单条步行指令。地图 Provider 会把高德/百度/本地路线统一转换成这个结构。
    index: int
    instruction: str
    distance_meters: float
    duration_seconds: int
    direction: str = "forward"
    action: str = "walk"


class RouteRequest(BaseModel):
    # 明确目的地路线请求，例如“从当前位置去德和园”。
    session_id: str
    origin: GeoPoint
    destination: DestinationRef
    strategy: Literal["walking"] = "walking"
    language: str = "zh"


class NearestRequest(BaseModel):
    # 最近服务点路线请求，例如“最近厕所/出口/服务中心”。
    session_id: str
    origin: GeoPoint
    target_type: str
    radius_meters: float = 1000


class RouteResponse(BaseModel):
    # 初始路线规划结果。前端地图画 polyline，底部卡片显示距离和 step。
    task_id: str
    destination_name: str
    distance_meters: float
    duration_seconds: int
    polyline: list[GeoPoint]
    steps: list[RouteStep]
    tts_text: str


class NavigationUpdateRequest(BaseModel):
    # 导航中上传当前位置，触发 step 推进、到达判断和偏航判断。
    session_id: str
    task_id: str
    location: GeoPoint
    heading: float | None = None


class NavigationUpdateResponse(BaseModel):
    # update-position 的即时返回；同样会通过 WebSocket 广播给客户端。
    status: str
    current_step_index: int
    instruction: str
    distance_to_next_step_meters: float
    distance_to_destination_meters: float
    off_route: bool
    tts_text: str


class StopNavigationRequest(BaseModel):
    # 停止导航时 task_id 可选；不传则停止当前 session 的活动任务。
    session_id: str
    task_id: str | None = None


class NavigationState(BaseModel):
    # Redis 中的实时导航状态。它比数据库 navigation_task 更新更频繁。
    task_id: str
    session_id: str
    status: str
    destination_name: str
    destination_poi_id: int | None = None
    provider: str
    current_step_index: int = 0
    distance_to_next_step_meters: float | None = None
    distance_to_destination_meters: float | None = None
    off_route: bool = False
    off_route_count: int = 0
    last_instruction: str | None = None
    last_location: GeoPoint | None = None
    route_distance_meters: float
    route_duration_seconds: int
    route_polyline: list[GeoPoint] = Field(default_factory=list)
    updated_at: float
