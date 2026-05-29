from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.photo import PhotoAssetRead, PhotoCaptureRequest
from app.services.photo.photo_service import PhotoService

router = APIRouter(prefix="/photo", tags=["photo"])


@router.post("/capture", response_model=PhotoAssetRead)
def capture(payload: PhotoCaptureRequest, db: Session = Depends(get_db)):
    return PhotoService(db).capture(payload)


@router.get("/session/{session_id}", response_model=list[PhotoAssetRead])
def list_session(session_id: str, db: Session = Depends(get_db)):
    return PhotoService(db).list_by_session(session_id)
