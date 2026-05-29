from sqlalchemy.orm import Session
from app.repositories.poi_repo import POIRepository, poi_to_schema
from app.schemas.location import GeoPoint
from app.schemas.poi import POICandidate
from app.services.map.coordinate import angle_delta, bearing_degree, haversine_meters


class FovService:
    def __init__(self, db: Session):
        self.poi_repo = POIRepository(db)

    def get_visible_poi_candidates(self, current_location: GeoPoint, heading: float, fov_degree: float = 60, max_distance_meters: float = 120, visual_confidence: dict[int, float] | None = None) -> list[POICandidate]:
        visual_confidence = visual_confidence or {}
        candidates: list[POICandidate] = []
        for poi, distance in self.poi_repo.nearby(current_location, radius_meters=max_distance_meters):
            bearing = bearing_degree(current_location, GeoPoint(lng=poi.longitude, lat=poi.latitude))
            delta = angle_delta(heading, bearing)
            if delta > max(45, fov_degree / 2):
                continue
            distance_score = 1.0 if distance < 30 else 0.7 if distance < 80 else 0.4
            heading_score = 1.0 if delta < 15 else 0.7 if delta < 30 else 0.4
            priority_score = min(poi.priority / 10, 1.0)
            vision_score = visual_confidence.get(poi.id, 0.0)
            score = distance_score * 0.35 + heading_score * 0.35 + priority_score * 0.15 + vision_score * 0.15
            candidates.append(POICandidate(poi=poi_to_schema(poi), distance_meters=round(distance, 1), bearing_degree=round(bearing, 1), heading_delta_degree=round(delta, 1), score=round(score, 3), confidence=round(score, 3)))
        return sorted(candidates, key=lambda c: c.score, reverse=True)
