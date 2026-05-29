from typing import TypedDict


class GuideAgentState(TypedDict, total=False):
    session_id: str
    user_text: str | None
    input_type: str
    location: dict | None
    heading: float | None
    current_poi_id: int | None
    detected_pois: list[dict]
    detected_gestures: list[dict]
    intent: str | None
    slots: dict
    tool_result: dict | None
    response_text: str | None
    tts_text: str | None
    navigation_task_id: str | None
