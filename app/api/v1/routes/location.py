from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.repositories.device_repo import DeviceRepository
from app.schemas.location import LocationState, LocationUpdateRequest
from app.services.location.location_service import location_store
from app.services.realtime.connection_manager import connection_manager

router = APIRouter(prefix="/location", tags=["location"])


@router.post("/update", response_model=LocationState)
async def update_location(payload: LocationUpdateRequest, db: Session = Depends(get_db)):
    DeviceRepository(db).update_location(payload)
    state = location_store.update(payload)
    await connection_manager.broadcast(
        payload.session_id,
        {
            "type": "location_updated",
            "session_id": payload.session_id,
            "device_id": payload.device_id,
            "location": state,
        },
    )
    return state


@router.get("/current/{session_id}", response_model=LocationState)
def current_location(session_id: str):
    state = location_store.get(session_id)
    if not state:
        raise AppError("当前会话还没有位置", 404)
    return state
