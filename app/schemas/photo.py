from pydantic import BaseModel


class PhotoCaptureRequest(BaseModel):
    session_id: str
    device_id: str | None = None
    frame_id: str | None = None
    related_poi_id: int | None = None


class PhotoAssetRead(BaseModel):
    asset_id: str
    session_id: str
    device_id: str | None = None
    file_path: str | None = None
    related_poi_id: int | None = None
