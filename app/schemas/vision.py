from pydantic import BaseModel
from app.schemas.gesture import GestureAction, GestureResult


class DetectedPOI(BaseModel):
    poi_id: int
    name: str
    confidence: float
    bbox: list[int] | None = None


class VisionAnalyzeResponse(BaseModel):
    detected_pois: list[DetectedPOI]
    detected_gestures: list[GestureResult]
    actions: list[GestureAction]
    explanation_triggered: bool = False


class AnalyzeFramesRequest(BaseModel):
    session_id: str
    device_id: str
    frame_ids: list[str] = []
    mock_gesture: str | None = None
