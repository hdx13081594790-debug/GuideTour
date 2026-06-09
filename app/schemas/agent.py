from pydantic import BaseModel, Field
from app.schemas.common import ActionResult
from app.schemas.location import GeoPoint
from app.schemas.navigation import RouteResponse

# Agent 接口的数据契约。
#
# 前端问答框 POST /api/v1/agent/chat 时发送 AgentChatRequest；
# GuideAgent 返回 AgentChatResponse。
# route/actions/source_chunks 都是可选字段，前端根据是否存在决定：
# - 显示普通回答；
# - 启动导航；
# - 展示来源片段或建议问题。


class AgentChatRequest(BaseModel):
    # 用户输入 + 环境上下文。
    # location/heading/current_poi/detected_pois 帮助模型理解“这里/这个建筑”。
    session_id: str
    device_id: str | None = None
    text: str
    location: GeoPoint | None = None
    heading: float | None = None
    language: str = "zh"
    current_poi_id: int | None = None
    detected_pois: list[dict] = Field(default_factory=list)


class AgentChatResponse(BaseModel):
    # 统一响应格式。即使只是普通聊天，也返回 intent/response_text/tts_text。
    intent: str
    response_text: str
    tts_text: str
    actions: list[ActionResult] = Field(default_factory=list)
    route: RouteResponse | None = None
    source_chunks: list[dict] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)


class ExplainNearbyRequest(BaseModel):
    # 自动讲解请求：没有用户文本，主要依赖位置、朝向和定位精度。
    session_id: str
    device_id: str | None = None
    location: GeoPoint
    heading: float
    language: str = "zh"
    style: str = "normal"
    accuracy_meters: float | None = None


class ExplainNearbyResponse(BaseModel):
    # 自动讲解响应：前端/眼镜端可以直接播放 tts_text。
    poi_id: int | None = None
    poi_name: str | None = None
    confidence: float
    explanation: str
    suggested_questions: list[str]
    tts_text: str
