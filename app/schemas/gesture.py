from typing import Literal
from pydantic import BaseModel

# 手势识别数据契约。
#
# Vision/Gesture 服务输出 GestureResult；
# GestureService.decide_action() 再把稳定手势转换成 GestureAction。
# 前端/眼镜端根据 action.type 决定拍照、翻页、停止导航或进入提问。


GestureName = Literal[
    "take_photo",
    "navigate_forward",
    "swipe_left",
    "swipe_right",
    "stop_navigation",
    "wake_question",
]


class GestureResult(BaseModel):
    # 单个识别结果。duration_ms 和 confidence 用于防误触。
    gesture: GestureName
    confidence: float
    bbox: list[int] | None = None
    duration_ms: int | None = None


class GestureAction(BaseModel):
    # 手势触发后的业务动作描述。
    type: str
    status: str
    message: str
    requires_confirmation: bool = False
