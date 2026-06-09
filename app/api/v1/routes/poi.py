from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.repositories.poi_repo import POIRepository, poi_to_schema
from app.schemas.location import GeoPoint
from app.schemas.poi import POICandidate, POIRead, POISearchResponse
from app.services.navigation.navigation_service import get_map_provider

# POI 路由。
#
# 这里提供“点位查询”能力：
# - search：名称/类型搜索，本地没有时可调用地图 Provider；
# - nearby：按当前位置找附近 POI；
# - get：按 id 获取单个 POI。
#
# NavigationService 和前端调试页都会依赖这些点位数据。

router = APIRouter(prefix="/poi", tags=["poi"])


@router.get("/search", response_model=POISearchResponse)
async def search_poi(
    q: str | None = None,
    poi_type: str | None = None,
    lng: float | None = None,
    lat: float | None = None,
    radius_meters: int = 1000,
    db: Session = Depends(get_db),
):
    # 优先查本地 POI 表。本地没有结果且有查询词时，再请求地图 Provider。
    local_items = [poi_to_schema(p) for p in POIRepository(db).search(query=q, poi_type=poi_type)]
    if local_items or not q:
        return POISearchResponse(items=local_items)
    location = GeoPoint(lng=lng, lat=lat) if lng is not None and lat is not None else None
    provider_items = await get_map_provider().search_poi(q, location=location, radius=radius_meters)
    return POISearchResponse(items=provider_items)


@router.get("/nearby", response_model=list[POICandidate])
def nearby_poi(lng: float, lat: float, poi_type: str | None = None, radius_meters: float = 1000, db: Session = Depends(get_db)):
    # nearby 返回 POICandidate，带距离和粗略置信度，方便前端或 FovService 展示候选。
    origin = GeoPoint(lng=lng, lat=lat)
    return [
        POICandidate(poi=poi_to_schema(p), distance_meters=round(d, 1), score=max(0, 1 - d / radius_meters), confidence=max(0, 1 - d / radius_meters))
        for p, d in POIRepository(db).nearby(origin, poi_type=poi_type, radius_meters=radius_meters)
    ]


@router.get("/{poi_id}", response_model=POIRead)
def get_poi(poi_id: int, db: Session = Depends(get_db)):
    # 单点详情查询。找不到时统一抛 AppError。
    poi = POIRepository(db).get(poi_id)
    if not poi:
        raise AppError("POI 不存在", 404)
    return poi_to_schema(poi)
