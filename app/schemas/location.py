from typing import Literal
from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    lng: float
    lat: float
    coord_type: Literal["wgs84", "gcj02", "bd09"] = "gcj02"


class LocationUpdateRequest(BaseModel):
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
    session_id: str
    device_id: str | None = None
    location: GeoPoint | None = None
    heading: float | None = None
    pitch: float | None = None
    roll: float | None = None
    accuracy_meters: float | None = None
