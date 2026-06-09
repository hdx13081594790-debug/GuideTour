from pydantic import BaseModel

# 拍照资产数据契约。
#
# 手势或前端按钮发起 PhotoCaptureRequest；
# PhotoService 创建 photo_asset；
# 前端通过 PhotoAssetRead 展示纪念册/拍照结果。


class PhotoCaptureRequest(BaseModel):
    # frame_id 可关联眼镜上传的关键帧。
    session_id: str
    device_id: str | None = None
    frame_id: str | None = None
    related_poi_id: int | None = None


class PhotoAssetRead(BaseModel):
    # 返回给前端的照片资产摘要。
    asset_id: str
    session_id: str
    device_id: str | None = None
    file_path: str | None = None
    related_poi_id: int | None = None
