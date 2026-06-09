from pydantic import BaseModel
from app.schemas.gesture import GestureAction, GestureResult

# 视觉分析数据契约。
#
# 眼镜端上传图片/帧序列；
# VisionService 识别画面中的 POI；
# GestureService 识别手势并输出动作；
# VisionAnalyzeResponse 汇总给前端/Agent。


class DetectedPOI(BaseModel):
    # 画面中的建筑/景点检测结果。
    poi_id: int
    name: str
    confidence: float
    bbox: list[int] | None = None


class VisionAnalyzeResponse(BaseModel):
    # 单帧/多帧视觉分析统一响应。
    detected_pois: list[DetectedPOI]
    detected_gestures: list[GestureResult]
    actions: list[GestureAction]
    explanation_triggered: bool = False


class AnalyzeFramesRequest(BaseModel):
    # 多帧 mock 分析请求。MVP 用 mock_gesture 直接模拟手势。
    session_id: str
    device_id: str
    frame_ids: list[str] = []
    mock_gesture: str | None = None
