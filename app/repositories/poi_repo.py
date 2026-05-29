from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models.poi import POI
from app.schemas.location import GeoPoint
from app.schemas.poi import POIRead
from app.services.map.coordinate import haversine_meters


def poi_to_schema(poi: POI) -> POIRead:
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
        stmt = select(POI)
        if poi_type:
            stmt = stmt.where(POI.poi_type == poi_type)
        if query:
            like = f"%{query}%"
            stmt = stmt.where(or_(POI.name.like(like), POI.alias_names.like(like), POI.description.like(like)))
        return list(self.db.execute(stmt.order_by(POI.priority.desc()).limit(limit)).scalars())

    def nearby(self, origin: GeoPoint, poi_type: str | None = None, radius_meters: float = 1000) -> list[tuple[POI, float]]:
        rows = self.search(poi_type=poi_type, limit=500)
        ranked = []
        for poi in rows:
            distance = haversine_meters(origin, GeoPoint(lng=poi.longitude, lat=poi.latitude))
            if distance <= radius_meters:
                ranked.append((poi, distance))
        return sorted(ranked, key=lambda item: item[1])
