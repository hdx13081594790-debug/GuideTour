import json
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.schemas.agent import AgentChatRequest

# 这个文件只负责“调用 DeepSeek 并拿到结构化决策”，不直接执行业务工具。
# 这样可以把 LLM 的不确定性关在 AgentDecision 这一层：
# DeepSeek 只说 action/destination/reply，真正能不能导航、怎么导航，
# 仍由 GuideAgent 和 NavigationService 按后端规则执行。
#
# 数据流：
# AgentChatRequest + 当前 POI 列表
# -> DeepSeek Chat Completions
# -> JSON 字符串
# -> AgentDecision(Pydantic 校验)
# -> GuideAgent 根据 action 调工具或直接回复。

AgentDecisionAction = Literal[
    "NAVIGATE_TO_POI",
    "NAVIGATE_NEAREST_SERVICE",
    "EXPLAIN_NEARBY",
    "ASK_HISTORY",
    "TAKE_PHOTO",
    "STOP_NAVIGATION",
    "CHAT",
]


class AgentDecision(BaseModel):
    # LLM 给后端的“工具调用计划”。
    # action 决定下一步走哪个分支；
    # reply 是不需要工具或需要澄清时给用户看的自然语言；
    # destination_* 是导航工具需要的槽位。
    action: AgentDecisionAction
    reply: str
    destination_name: str | None = None
    destination_type: str | None = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    needs_clarification: bool = False


class DeepSeekAgentClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.deepseek_api_key)

    async def decide(self, request: AgentChatRequest, poi_names: list[str]) -> AgentDecision:
        # 这里调用的是 DeepSeek 的 OpenAI-compatible /chat/completions。
        # response_format=json_object 要求模型尽量返回 JSON，后面仍用
        # Pydantic 做二次校验，避免模型输出格式漂移直接污染业务层。
        if not self.settings.deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured")

        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": self._system_prompt(poi_names)},
                {"role": "user", "content": self._user_prompt(request)},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        url = self.settings.deepseek_base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        return self._parse_decision(content)

    def _parse_decision(self, content: str) -> AgentDecision:
        # 把模型文本变成强类型对象。这里兼容 intent/UNKNOWN 是为了
        # 后续换模型或 prompt 调整时，减少接口字段小变化带来的崩溃。
        try:
            raw: dict[str, Any] = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"DeepSeek returned non-JSON content: {content[:200]}") from exc

        if "action" not in raw and "intent" in raw:
            raw["action"] = raw["intent"]
        if raw.get("action") == "UNKNOWN":
            raw["action"] = "CHAT"
        return AgentDecision.model_validate(raw)

    def _system_prompt(self, poi_names: list[str]) -> str:
        # Prompt 的关键约束：
        # “只有明确路线需求才导航”。普通问答必须留在聊天分支，
        # 这能避免用户问历史故事时误触发路线规划。
        poi_text = "、".join(poi_names[:80]) or "德和园、仁寿殿、佛香阁、长廊、昆明湖、厕所、出口"
        return f"""
你是颐和园 AI 导览眼镜的后端 Agent。你必须根据游客输入，自主判断是否需要调用导航工具。

可用 POI 名称包括：{poi_text}

只允许输出 JSON，不要输出 Markdown。JSON 字段：
{{
  "action": "NAVIGATE_TO_POI | NAVIGATE_NEAREST_SERVICE | EXPLAIN_NEARBY | ASK_HISTORY | TAKE_PHOTO | STOP_NAVIGATION | CHAT",
  "reply": "给游客看的自然语言回答",
  "destination_name": "要导航到的具体 POI 名称，没有则为 null",
  "destination_type": "toilet | exit | entrance | medical | service_center | scenic_spot | null",
  "confidence": 0.0,
  "needs_clarification": false
}}

决策规则：
1. 只有游客明确表达“带我去、我要去、怎么去、最近厕所/出口/服务中心”等路线需求时，才选择导航 action。
2. 普通聊天、历史文化问题、景点问答、闲聊都不要规划路线，选择 CHAT 或 ASK_HISTORY，并在 reply 中直接回答。
3. “这个建筑有什么故事”“它为什么有三层”“慈禧为什么喜欢这里”属于 ASK_HISTORY，不要导航。
4. “介绍一下这里”“我现在看到的是什么”属于 EXPLAIN_NEARBY。
5. 如果要找最近厕所，action=NAVIGATE_NEAREST_SERVICE，destination_type=toilet。
6. 如果要去具体景点，action=NAVIGATE_TO_POI，destination_name 填最可能的 POI 名。
7. 如果目的地不清楚，needs_clarification=true，并在 reply 中反问，不要编造目的地。
8. 回答要简洁，适合手机导览端阅读。
""".strip()

    def _user_prompt(self, request: AgentChatRequest) -> str:
        # 用户输入不是单独一行文本，而是带上下文发给模型：
        # location/heading/current_poi/detected_pois 会帮助模型判断
        # “这里”“这个建筑”“前方建筑”到底指什么。
        context = {
            "user_text": request.text,
            "location": request.location.model_dump() if request.location else None,
            "heading": request.heading,
            "current_poi_id": request.current_poi_id,
            "detected_pois": request.detected_pois,
            "language": request.language,
        }
        return json.dumps(context, ensure_ascii=False)
