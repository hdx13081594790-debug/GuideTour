from typing import Literal
from pydantic import BaseModel


GestureName = Literal[
    "take_photo",
    "navigate_forward",
    "swipe_left",
    "swipe_right",
    "stop_navigation",
    "wake_question",
]


class GestureResult(BaseModel):
    gesture: GestureName
    confidence: float
    bbox: list[int] | None = None
    duration_ms: int | None = None


class GestureAction(BaseModel):
    type: str
    status: str
    message: str
    requires_confirmation: bool = False
