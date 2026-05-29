import time
from app.schemas.gesture import GestureAction, GestureResult


class GestureService:
    def __init__(self) -> None:
        self._last_trigger_at: dict[str, float] = {}

    async def detect(self, frame: bytes, mock_gesture: str | None = None) -> list[GestureResult]:
        if not mock_gesture:
            return []
        return [GestureResult(gesture=mock_gesture, confidence=0.91, duration_ms=1000)]

    async def decide_action(self, gestures: list[GestureResult], session_context: dict) -> list[GestureAction]:
        actions: list[GestureAction] = []
        session_id = session_context.get("session_id", "default")
        now = time.monotonic()
        for item in gestures:
            key = f"{session_id}:{item.gesture}"
            if item.confidence < 0.75 or (item.duration_ms or 0) < 800:
                continue
            if now - self._last_trigger_at.get(key, 0) < 3:
                continue
            self._last_trigger_at[key] = now
            if item.gesture == "take_photo":
                actions.append(GestureAction(type="photo", status="triggered", message="已拍照，稍后可在纪念册中查看。"))
            elif item.gesture == "navigate_forward":
                poi_name = session_context.get("detected_poi_name", "前方建筑")
                actions.append(GestureAction(type="navigation_confirm", status="waiting_confirm", message=f"检测到你指向{poi_name}，要为你导航过去吗？", requires_confirmation=True))
            elif item.gesture == "stop_navigation":
                actions.append(GestureAction(type="stop_navigation", status="triggered", message="已停止导航。", requires_confirmation=True))
            elif item.gesture in {"swipe_left", "swipe_right"}:
                actions.append(GestureAction(type="page", status="triggered", message="已切换到下一段。"))
            elif item.gesture == "wake_question":
                actions.append(GestureAction(type="wake_question", status="triggered", message="我在听，你可以问我关于这里的问题。"))
        return actions
