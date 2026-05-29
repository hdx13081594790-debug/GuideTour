from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.poi_repo import POIRepository, poi_to_schema
from app.schemas.location import GeoPoint
from app.schemas.poi import POICandidate, POIRead, POISearchResponse
from app.services.map.coordinate import haversine_meters

router = APIRouter(prefix="/poi", tags=["poi"])


@router.get("/search", response_model=POISearchResponse)
def search_poi(q: str | None = None, poi_type: str | None = None, db: Session = Depends(get_db)):
    return POISearchResponse(items=[poi_to_schema(p) for p in POIRepository(db).search(query=q, poi_type=poi_type)])


@router.get("/nearby", response_model=list[POICandidate])
def nearby_poi(lng: float, lat: float, poi_type: str | None = None, radius_meters: float = 1000, db: Session = Depends(get_db)):
    origin = GeoPoint(lng=lng, lat=lat)
    return [
        POICandidate(poi=poi_to_schema(p), distance_meters=round(d, 1), score=max(0, 1 - d / radius_meters), confidence=max(0, 1 - d / radius_meters))
        for p, d in POIRepository(db).nearby(origin, poi_type=poi_type, radius_meters=radius_meters)
    ]


@router.get("/{poi_id}", response_model=POIRead)
def get_poi(poi_id: int, db: Session = Depends(get_db)):
    poi = POIRepository(db).get(poi_id)
    if not poi:
        from app.core.exceptions import AppError
        raise AppError("POI 不存在", 404)
    return poi_to_schema(poi)
