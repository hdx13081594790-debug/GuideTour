from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.photo import PhotoAssetRead, PhotoCaptureRequest
from app.services.photo.photo_service import PhotoService

# 拍照路由。
#
# 目前由手势识别或前端调试按钮触发，创建 photo_asset 记录。
# 真实图片存储后续可在 PhotoService 中接入对象存储，不影响路由层。

router = APIRouter(prefix="/photo", tags=["photo"])


@router.post("/capture", response_model=PhotoAssetRead)
def capture(payload: PhotoCaptureRequest, db: Session = Depends(get_db)):
    # 创建一条照片资产记录。
    return PhotoService(db).capture(payload)


@router.get("/session/{session_id}", response_model=list[PhotoAssetRead])
def list_session(session_id: str, db: Session = Depends(get_db)):
    # 获取某个会话的照片列表，可用于后续“游览纪念册”。
    return PhotoService(db).list_by_session(session_id)
