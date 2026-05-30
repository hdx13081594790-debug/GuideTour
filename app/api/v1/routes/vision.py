from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.location import GeoPoint
from app.schemas.vision import AnalyzeFramesRequest, VisionAnalyzeResponse
from app.services.photo.photo_service import PhotoService
from app.schemas.photo import PhotoCaptureRequest
from app.services.vision.gesture_service import GestureService
from app.services.vision.vision_service import VisionService
from app.services.realtime.connection_manager import connection_manager

router = APIRouter(prefix="/vision", tags=["vision"])
gesture_service = GestureService()


@router.post("/analyze-frame", response_model=VisionAnalyzeResponse)
async def analyze_frame(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    device_id: str = Form(...),
    lng: float | None = Form(None),
    lat: float | None = Form(None),
    heading: float | None = Form(None),
    mock_gesture: str | None = Form(None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    location = GeoPoint(lng=lng, lat=lat) if lng is not None and lat is not None else None
    detected_pois = await VisionService(db).analyze_frame(content, location, heading)
    gestures = await gesture_service.detect(content, mock_gesture)
    context = {"session_id": session_id, "detected_poi_name": detected_pois[0].name if detected_pois else None}
    actions = await gesture_service.decide_action(gestures, context)
    for action in actions:
        if action.type == "photo":
            PhotoService(db).capture(PhotoCaptureRequest(session_id=session_id, device_id=device_id, related_poi_id=detected_pois[0].poi_id if detected_pois else None))
    response = VisionAnalyzeResponse(detected_pois=detected_pois, detected_gestures=gestures, actions=actions, explanation_triggered=bool(detected_pois))
    await connection_manager.broadcast(session_id, {"type": "vision_analyzed", "session_id": session_id, "device_id": device_id, "result": response})
    return response


@router.post("/analyze-frames", response_model=VisionAnalyzeResponse)
async def analyze_frames(payload: AnalyzeFramesRequest, db: Session = Depends(get_db)):
    detected_pois = await VisionService(db).analyze_frame(b"", None, None)
    gestures = await gesture_service.detect(b"", payload.mock_gesture)
    actions = await gesture_service.decide_action(gestures, {"session_id": payload.session_id, "detected_poi_name": detected_pois[0].name if detected_pois else None})
    response = VisionAnalyzeResponse(detected_pois=detected_pois, detected_gestures=gestures, actions=actions, explanation_triggered=bool(detected_pois))
    await connection_manager.broadcast(payload.session_id, {"type": "vision_analyzed", "session_id": payload.session_id, "device_id": payload.device_id, "result": response})
    return response


@router.post("/gesture")
async def gesture(payload: AnalyzeFramesRequest):
    gestures = await gesture_service.detect(b"", payload.mock_gesture)
    actions = await gesture_service.decide_action(gestures, {"session_id": payload.session_id})
    result = {"detected_gestures": gestures, "actions": actions}
    await connection_manager.broadcast(payload.session_id, {"type": "gesture_detected", "session_id": payload.session_id, "device_id": payload.device_id, "result": result})
    return result
