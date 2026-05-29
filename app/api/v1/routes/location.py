from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.exceptions import AppError
from app.db.session import get_db
from app.repositories.device_repo import DeviceRepository
from app.schemas.location import LocationState, LocationUpdateRequest
from app.services.location.location_service import location_store

router = APIRouter(prefix="/location", tags=["location"])


@router.post("/update", response_model=LocationState)
def update_location(payload: LocationUpdateRequest, db: Session = Depends(get_db)):
    DeviceRepository(db).update_location(payload)
    return location_store.update(payload)


@router.get("/current/{session_id}", response_model=LocationState)
def current_location(session_id: str):
    state = location_store.get(session_id)
    if not state:
        raise AppError("当前会话还没有位置", 404)
    return state
