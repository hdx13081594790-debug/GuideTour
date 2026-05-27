from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class POI(BaseModel):
    id: str
    name: str
    name_en: str
    x: float
    y: float
    tags: list[str]
    open_time: str
    visit_minutes: int
    image_url: str
    summary: str
    story: str


class POIInput(BaseModel):
    id: str = Field(min_length=2)
    name: str = Field(min_length=1)
    name_en: str = ""
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    tags: list[str] = []
    open_time: str = "08:30-17:00"
    visit_minutes: int = Field(default=20, ge=5, le=180)
    image_url: str = ""
    summary: str = ""
    story: str = ""


class Edge(BaseModel):
    from_poi_id: str
    to_poi_id: str
    distance_m: int
    walk_minutes: int
    recommended: bool = True


class KnowledgeDoc(BaseModel):
    id: str
    title: str
    poi_id: str | None = None
    language: str = "zh"
    content: str
    tags: list[str] = []


class AsrResponse(BaseModel):
    language: str
    transcript: str
    confidence: float
    note: str


class ChatRequest(BaseModel):
    session_id: str = "demo-session"
    message: str
    language: str | None = None
    current_poi_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    language: str
    answer: str
    citations: list[dict[str, Any]] = []
    suggested_actions: list[dict[str, Any]] = []
    intent: str


class RouteRequest(BaseModel):
    start_poi_id: str
    end_poi_id: str | None = None
    duration_minutes: int = Field(default=90, ge=20, le=480)
    interests: list[str] = []


class RouteStop(BaseModel):
    poi_id: str
    name: str
    arrive_after_minutes: int
    stay_minutes: int
    summary: str
    tags: list[str]


class RouteResponse(BaseModel):
    route_id: str
    total_minutes: int
    total_distance_m: int
    stops: list[RouteStop]
    narrative: str


class VisionResponse(BaseModel):
    language: str
    candidates: list[dict[str, Any]]
    explanation: str
    suggested_questions: list[str]
