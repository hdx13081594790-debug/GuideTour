import time
from app.schemas.gesture import GestureAction, GestureResult

# 手势服务。
#
# detect() 负责从画面帧中识别手势；
# decide_action() 负责把稳定手势转换成业务动作。
#
# 当前 detect 是 mock：通过 mock_gesture 直接返回识别结果。
# 防误触规则在 decide_action 中体现：置信度阈值、持续时间、冷却时间。


class GestureService:
    def __init__(self) -> None:
        self._last_trigger_at: dict[str, float] = {}

    async def detect(self, frame: bytes, mock_gesture: str | None = None) -> list[GestureResult]:
        # TODO: 接真实手势模型。MVP 用 mock_gesture 模拟连续识别结果。
        if not mock_gesture:
            return []
        return [GestureResult(gesture=mock_gesture, confidence=0.91, duration_ms=1000)]

    async def decide_action(self, gestures: list[GestureResult], session_context: dict) -> list[GestureAction]:
        # 将“识别结果”升级为“业务动作”。
        # 这里集中处理冷却时间，避免同一手势连续触发多次拍照/停止导航。
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
