from pydantic import BaseModel
from app.schemas.location import GeoPoint

# POI 数据契约。
#
# POI 在系统里既是“地图点”，也是“讲解对象”和“导航目的地”。
# Repository 从数据库模型 POI 转成这些 Pydantic 模型后，再返回给 API/服务层。


class POIBase(BaseModel):
    # 前端和服务层关心的 POI 核心字段。
    name: str
    poi_type: str
    location: GeoPoint
    description: str | None = ""
    priority: int = 5
    alias_names: list[str] = []


class POIRead(POIBase):
    # 从数据库读取后的完整 POI 响应。
    id: int
    area_name: str | None = None
    is_accessible: bool = True
    opening_status: str = "open"


class POICandidate(BaseModel):
    # FovService 计算出来的视野候选，包含距离、方位角、置信分。
    poi: POIRead
    distance_meters: float
    bearing_degree: float | None = None
    heading_delta_degree: float | None = None
    score: float
    confidence: float = 0.0


class POISearchResponse(BaseModel):
    # /poi/search 的列表响应容器。
    items: list[POIRead]
