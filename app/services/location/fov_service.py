from sqlalchemy.orm import Session
from app.repositories.poi_repo import POIRepository, poi_to_schema
from app.schemas.location import GeoPoint
from app.schemas.poi import POICandidate
from app.services.map.coordinate import angle_delta, bearing_degree, haversine_meters

# FovService 用来判断“游客正在看哪里”。
#
# 输入是当前位置 GeoPoint 和眼镜/手机朝向 heading；
# 输出是按 score 排序的 POI 候选。
#
# score 由四类信息组成：
# - 距离：越近越可能被看到；
# - 朝向夹角：越接近视线方向分越高；
# - POI 优先级：重要景点更容易触发讲解；
# - 视觉置信度：如果视觉模型识别到同一建筑，可额外加分。
#
# Agent 的“介绍一下这里”和 /agent/explain-nearby 都会走这里。


class FovService:
    def __init__(self, db: Session):
        self.poi_repo = POIRepository(db)

    def get_visible_poi_candidates(self, current_location: GeoPoint, heading: float, fov_degree: float = 60, max_distance_meters: float = 120, visual_confidence: dict[int, float] | None = None) -> list[POICandidate]:
        # MVP 阶段没有三维建筑遮挡和真实相机视锥，只用 2D 方位角近似。
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
