from sqlalchemy.orm import Session
from app.repositories.poi_repo import POIRepository
from app.schemas.location import GeoPoint
from app.schemas.vision import DetectedPOI

# 视觉识别服务。
#
# 输入是眼镜上传的 frame bytes，以及可选的位置/朝向上下文；
# 输出是画面中检测到的 DetectedPOI。
#
# 当前是 mock 策略：
# - 如果有 location，返回附近最近 POI；
# - 如果没有 location，默认模拟识别德和园大戏楼。
# 后续可替换为 YOLO/CLIP/图像检索模型，接口保持不变。


class VisionService:
    def __init__(self, db: Session):
        self.poi_repo = POIRepository(db)

    async def analyze_frame(self, frame: bytes, location: GeoPoint | None = None, heading: float | None = None) -> list[DetectedPOI]:
        # 位置上下文能让 mock 结果更像真实“眼镜看到附近建筑”。
        if location:
            nearby = self.poi_repo.nearby(location, radius_meters=150)
            if nearby:
                poi = nearby[0][0]
                return [DetectedPOI(poi_id=poi.id, name=poi.name, confidence=0.88, bbox=[120, 80, 500, 420])]
        matches = self.poi_repo.search(query="德和园大戏楼", limit=1)
        if matches:
            poi = matches[0]
            return [DetectedPOI(poi_id=poi.id, name=poi.name, confidence=0.88, bbox=[120, 80, 500, 420])]
        return []
