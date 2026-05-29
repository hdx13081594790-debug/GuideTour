from pydantic import BaseModel, Field
from app.schemas.common import ActionResult
from app.schemas.location import GeoPoint
from app.schemas.navigation import RouteResponse


class AgentChatRequest(BaseModel):
    session_id: str
    device_id: str | None = None
    text: str
    location: GeoPoint | None = None
    heading: float | None = None
    language: str = "zh"
    current_poi_id: int | None = None
    detected_pois: list[dict] = Field(default_factory=list)


class AgentChatResponse(BaseModel):
    intent: str
    response_text: str
    tts_text: str
    actions: list[ActionResult] = Field(default_factory=list)
    route: RouteResponse | None = None
    source_chunks: list[dict] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)


class ExplainNearbyRequest(BaseModel):
    session_id: str
    device_id: str | None = None
    location: GeoPoint
    heading: float
    language: str = "zh"
    style: str = "normal"
    accuracy_meters: float | None = None


class ExplainNearbyResponse(BaseModel):
    poi_id: int | None = None
    poi_name: str | None = None
    confidence: float
    explanation: str
    suggested_questions: list[str]
    tts_text: str
