from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models.poi import POI
from app.schemas.location import GeoPoint
from app.schemas.poi import POIRead
from app.services.map.coordinate import haversine_meters

# POIRepository 是 POI 数据表的访问层。
#
# 数据流：
# SQLAlchemy POI 模型 <-> POIRead Pydantic 模型；
# NavigationService 用 search/nearby 找目的地；
# FovService 用 nearby 找视野范围内的候选景点。


def poi_to_schema(poi: POI) -> POIRead:
    # 把数据库字段转换成 API/服务层使用的结构。
    # alias_names 在数据库中是逗号分隔字符串，对外转换成 list[str]。
    aliases = [x.strip() for x in (poi.alias_names or "").split(",") if x.strip()]
    return POIRead(
        id=poi.id,
        name=poi.name,
        alias_names=aliases,
        poi_type=poi.poi_type,
        description=poi.description or "",
        location=GeoPoint(lng=poi.longitude, lat=poi.latitude),
        priority=poi.priority,
        area_name=poi.area_name,
        is_accessible=poi.is_accessible,
        opening_status=poi.opening_status,
    )


class POIRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, poi_id: int) -> POI | None:
        return self.db.get(POI, poi_id)

    def search(self, query: str | None = None, poi_type: str | None = None, limit: int = 20) -> list[POI]:
        # 支持按名称/别名/描述模糊搜索，也支持按 poi_type 过滤。
        stmt = select(POI)
        if poi_type:
            stmt = stmt.where(POI.poi_type == poi_type)
        if query:
            like = f"%{query}%"
            stmt = stmt.where(or_(POI.name.like(like), POI.alias_names.like(like), POI.description.like(like)))
        return list(self.db.execute(stmt.order_by(POI.priority.desc()).limit(limit)).scalars())

    def nearby(self, origin: GeoPoint, poi_type: str | None = None, radius_meters: float = 1000) -> list[tuple[POI, float]]:
        # MVP 直接从数据库取候选后用 haversine 计算直线距离。
        # 数据量大时可以改为空间索引或地图服务周边检索。
        rows = self.search(poi_type=poi_type, limit=500)
        ranked = []
        for poi in rows:
            distance = haversine_meters(origin, GeoPoint(lng=poi.longitude, lat=poi.latitude))
            if distance <= radius_meters:
                ranked.append((poi, distance))
        return sorted(ranked, key=lambda item: item[1])
