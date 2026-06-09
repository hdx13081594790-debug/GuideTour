from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.photo_asset import PhotoAsset
from app.schemas.photo import PhotoAssetRead, PhotoCaptureRequest

# PhotoService 负责拍照资产业务。
#
# 数据流：
# 手势/接口触发拍照 -> PhotoCaptureRequest
# -> 创建 photo_asset 记录
# -> 返回 PhotoAssetRead 给前端。
#
# MVP 中 file_path 是 mock://，后续接对象存储时在这里生成真实 URL。


class PhotoService:
    def __init__(self, db: Session):
        self.db = db

    def capture(self, payload: PhotoCaptureRequest) -> PhotoAssetRead:
        # 这里只创建资产记录，不真正处理图片二进制。
        # 真实眼镜画面可通过 frame_id 关联 FrameStore 或对象存储文件。
        asset = PhotoAsset(
            asset_id=f"photo_{uuid4().hex[:10]}",
            session_id=payload.session_id,
            device_id=payload.device_id,
            file_path=f"mock://frames/{payload.frame_id or 'current'}",
            related_poi_id=payload.related_poi_id,
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return PhotoAssetRead(asset_id=asset.asset_id, session_id=asset.session_id, device_id=asset.device_id, file_path=asset.file_path, related_poi_id=asset.related_poi_id)

    def list_by_session(self, session_id: str) -> list[PhotoAssetRead]:
        # 纪念册列表按创建时间倒序返回。
        rows = self.db.execute(select(PhotoAsset).where(PhotoAsset.session_id == session_id).order_by(PhotoAsset.created_at.desc())).scalars()
        return [PhotoAssetRead(asset_id=a.asset_id, session_id=a.session_id, device_id=a.device_id, file_path=a.file_path, related_poi_id=a.related_poi_id) for a in rows]
