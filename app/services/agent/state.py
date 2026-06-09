from typing import TypedDict

# GuideAgentState 是为未来 LangGraph 工作流预留的状态结构。
#
# 如果后续把当前 GuideAgent.chat() 拆成多个节点：
# input_normalize -> context_load -> intent_router -> tool_execute -> response_generate，
# 每个节点之间就可以传递这个 TypedDict。
# 当前 MVP 还没有真正启用 LangGraph，但字段已经按计划保留。


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
