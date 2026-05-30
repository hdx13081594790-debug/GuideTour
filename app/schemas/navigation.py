from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.location import GeoPoint


class DestinationRef(BaseModel):
    poi_id: int | None = None
    name: str | None = None


class RouteStep(BaseModel):
    index: int
    instruction: str
    distance_meters: float
    duration_seconds: int
    direction: str = "forward"
    action: str = "walk"


class RouteRequest(BaseModel):
    session_id: str
    origin: GeoPoint
    destination: DestinationRef
    strategy: Literal["walking"] = "walking"
    language: str = "zh"


class NearestRequest(BaseModel):
    session_id: str
    origin: GeoPoint
    target_type: str
    radius_meters: float = 1000


class RouteResponse(BaseModel):
    task_id: str
    destination_name: str
    distance_meters: float
    duration_seconds: int
    polyline: list[GeoPoint]
    steps: list[RouteStep]
    tts_text: str


class NavigationUpdateRequest(BaseModel):
    session_id: str
    task_id: str
    location: GeoPoint
    heading: float | None = None


class NavigationUpdateResponse(BaseModel):
    status: str
    current_step_index: int
    instruction: str
    distance_to_next_step_meters: float
    distance_to_destination_meters: float
    off_route: bool
    tts_text: str


class StopNavigationRequest(BaseModel):
    session_id: str
    task_id: str | None = None


class NavigationState(BaseModel):
    task_id: str
    session_id: str
    status: str
    destination_name: str
    destination_poi_id: int | None = None
    provider: str
    current_step_index: int = 0
    distance_to_next_step_meters: float | None = None
    distance_to_destination_meters: float | None = None
    off_route: bool = False
    off_route_count: int = 0
    last_instruction: str | None = None
    last_location: GeoPoint | None = None
    route_distance_meters: float
    route_duration_seconds: int
    route_polyline: list[GeoPoint] = Field(default_factory=list)
    updated_at: float
