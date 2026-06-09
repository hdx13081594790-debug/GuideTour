from typing import Literal
from pydantic import BaseModel, Field

# 位置与姿态相关的数据契约。
#
# 项目内部统一使用 GeoPoint(lng, lat)，避免百度/高德坐标顺序混乱。
# coord_type 预留 wgs84/gcj02/bd09，MVP 阶段只做轻量适配。


class GeoPoint(BaseModel):
    # 所有后端服务之间传坐标都用这个模型。
    lng: float
    lat: float
    coord_type: Literal["wgs84", "gcj02", "bd09"] = "gcj02"


class LocationUpdateRequest(BaseModel):
    # 眼镜/手机端周期性上传的实时状态。
    # heading/pitch/roll 会被 FovService、自动讲解、导航提示使用。
    session_id: str
    device_id: str
    location: GeoPoint
    heading: float | None = Field(None, ge=0, le=360)
    pitch: float | None = None
    roll: float | None = None
    speed: float | None = None
    accuracy_meters: float | None = None
    timestamp: float | None = None


class LocationState(BaseModel):
    # 服务端保存的“最近一次位置状态”，通常来自 RedisLocationStore。
    session_id: str
    device_id: str | None = None
    location: GeoPoint | None = None
    heading: float | None = None
    pitch: float | None = None
    roll: float | None = None
    accuracy_meters: float | None = None
