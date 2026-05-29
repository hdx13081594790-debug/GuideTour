from pydantic import BaseModel
from app.schemas.location import GeoPoint


class POIBase(BaseModel):
    name: str
    poi_type: str
    location: GeoPoint
    description: str | None = ""
    priority: int = 5
    alias_names: list[str] = []


class POIRead(POIBase):
    id: int
    area_name: str | None = None
    is_accessible: bool = True
    opening_status: str = "open"


class POICandidate(BaseModel):
    poi: POIRead
    distance_meters: float
    bearing_degree: float | None = None
    heading_delta_degree: float | None = None
    score: float
    confidence: float = 0.0


class POISearchResponse(BaseModel):
    items: list[POIRead]
