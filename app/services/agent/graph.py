from sqlalchemy.orm import Session

from app.repositories.poi_repo import POIRepository
from app.repositories.session_repo import SessionRepository
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.schemas.common import ActionResult
from app.schemas.navigation import DestinationRef, RouteRequest
from app.schemas.photo import PhotoCaptureRequest
from app.services.agent.deepseek_client import AgentDecision, DeepSeekAgentClient
from app.services.agent.intent import classify_intent
from app.services.location.fov_service import FovService
from app.services.navigation.navigation_service import NavigationService
from app.services.photo.photo_service import PhotoService
from app.services.rag.mock_rag_client import MockRAGClient

# GuideAgent 是后端“导览大脑”的编排层。
# 它不直接处理 HTTP，也不直接操作前端 DOM，而是把一次用户输入转换为：
# 1. DeepSeek 决策；
# 2. 可选工具调用，例如导航、拍照、停止导航、视野讲解；
# 3. 统一的 AgentChatResponse。
#
# 数据流：
# POST /api/v1/agent/chat
# -> AgentChatRequest
# -> GuideAgent._decide()
# -> DeepSeekAgentClient.decide() 得到 AgentDecision
# -> 根据 action 调 NavigationService / PhotoService / FovService / RAG
# -> SessionRepository 写 interaction_log
# -> AgentChatResponse 返回前端。
#
# 注意：前端是否切换页面不是这里决定的。这里最多返回 route/actions；
# 前端 app.js 根据 response.intent 和 response.route 更新 UI。


class GuideAgent:
    def __init__(self, db: Session):
        # 一个 GuideAgent 实例服务一个 HTTP 请求。
        # db 是请求级 SQLAlchemy Session，Repository 和 Service 共用它，
        # 保证本次请求中的数据库读取/写入在同一个会话里完成。
        self.db = db
        self.poi_repo = POIRepository(db)
        self.nav = NavigationService(db)
        self.rag = MockRAGClient()
        self.llm = DeepSeekAgentClient()

    async def chat(self, request: AgentChatRequest) -> AgentChatResponse:
        # 第一步永远是“决策”，而不是直接查地图。
        # 这样 DeepSeek 可以先判断用户是真的要导航，还是只是聊天/问历史。
        decision = await self._decide(request)
        intent = decision.action
        tool_called = None
        related_poi_id = None

        if intent == "NAVIGATE_NEAREST_SERVICE":
            # 最近服务点导航：厕所、出口、入口、医疗点等。
            # 这里调用 NavigationService.nearest_route，它会先查本地 POI，
            # 必要时再走地图 Provider 搜索。
            destination_type = decision.destination_type or "toilet"
            if not request.location:
                response = self._text_response(intent, "请先同步当前位置，我再帮你规划最近路线。")
            else:
                route = await self.nav.nearest_route(request.session_id, request.location, destination_type)
                tool_called = "navigation_nearest"
                response = AgentChatResponse(
                    intent=intent,
                    response_text=route.tts_text,
                    tts_text=route.tts_text,
                    route=route,
                    actions=[ActionResult(type="navigation_started", task_id=route.task_id)],
                )

        elif intent == "NAVIGATE_TO_POI":
            # 指定景点导航：例如“带我去德和园”。
            # destination_name 来自 DeepSeek 抽取；如果用户说“那个建筑”，
            # 也可以用视觉识别 detected_pois 兜底。
            destination_name = decision.destination_name
            if not destination_name and request.detected_pois:
                destination_name = request.detected_pois[0].get("name")
            if not request.location or not destination_name or decision.needs_clarification:
                text = decision.reply or "我还不确定目的地。你可以说具体景点名，或者把视线对准建筑。"
                response = self._text_response(intent, text)
            else:
                route = await self.nav.plan_route(
                    RouteRequest(
                        session_id=request.session_id,
                        origin=request.location,
                        destination=DestinationRef(name=destination_name),
                    )
                )
                tool_called = "navigation_route"
                response = AgentChatResponse(
                    intent=intent,
                    response_text=route.tts_text,
                    tts_text=route.tts_text,
                    route=route,
                    actions=[ActionResult(type="navigation_started", task_id=route.task_id)],
                )

        elif intent == "EXPLAIN_NEARBY":
            # 附近讲解：不是路线工具，而是基于位置/朝向找视野候选 POI。
            response, related_poi_id, tool_called = await self._explain_nearby(request, decision)

        elif intent in {"ASK_HISTORY", "CHAT"}:
            # 普通问答和历史问题都不规划路线，直接把 DeepSeek 的 reply
            # 返回给问答栏。这里是避免“问故事却跳导航”的关键分支。
            related_poi_id = request.current_poi_id or (
                request.detected_pois[0].get("poi_id") if request.detected_pois else None
            )
            tool_called = "deepseek_chat" if self.llm.enabled else "rule_chat"
            text = decision.reply or "我可以继续回答你的问题，也可以帮你规划路线。"
            response = self._text_response(intent, text)

        elif intent == "TAKE_PHOTO":
            # 拍照动作目前是后端创建 photo_asset 记录；真正眼镜拍照/上传
            # 后续可以在 PhotoService 里接入设备 SDK 或对象存储。
            photo = PhotoService(self.db).capture(
                PhotoCaptureRequest(session_id=request.session_id, device_id=request.device_id)
            )
            tool_called = "photo_capture"
            text = "已拍照，稍后可在纪念册中查看。"
            response = AgentChatResponse(
                intent=intent,
                response_text=text,
                tts_text=text,
                actions=[ActionResult(type="photo", status="triggered", message=photo.asset_id)],
            )

        elif intent == "STOP_NAVIGATION":
            # 停止导航会取消当前 session 的活动任务，并更新 Redis 导航状态。
            task_id = self.nav.stop(request.session_id)
            tool_called = "navigation_stop"
            text = "已停止导航。"
            response = AgentChatResponse(
                intent=intent,
                response_text=text,
                tts_text=text,
                actions=[ActionResult(type="navigation_stopped", status="triggered", task_id=task_id)],
            )

        else:
            response = self._text_response("CHAT", decision.reply or "我可以帮你导航、讲解附近景点，或者回答颐和园历史问题。")

        SessionRepository(self.db).log(
            # 所有对话都写 interaction_log，方便后续做用户行为分析、
            # 调试模型误判、复盘工具调用链路。
            request.session_id,
            request.device_id,
            "text",
            request.text,
            response.intent,
            tool_called,
            response.response_text,
            related_poi_id,
        )
        return response

    async def _decide(self, request: AgentChatRequest) -> AgentDecision:
        # 优先走 DeepSeek。若本地没有 key、网络不可用、模型返回非 JSON，
        # 且 DEEPSEEK_FALLBACK_TO_RULES=true，则回退到旧的规则识别，
        # 保证演示环境至少可用。
        if self.llm.enabled:
            try:
                poi_names = [poi.name for poi in self.poi_repo.search(limit=200)]
                return await self.llm.decide(request, poi_names)
            except Exception:
                if not self.llm.settings.deepseek_fallback_to_rules:
                    raise

        intent, slots = classify_intent(request.text)
        # 规则兜底只用于开发/离线场景。线上要看真实 Agent 效果，
        # 可以把 DEEPSEEK_FALLBACK_TO_RULES=false，让错误直接暴露。
        if intent == "ASK_HISTORY":
            answer = await self.rag.answer(request.text, poi_id=request.current_poi_id)
            return AgentDecision(action=intent, reply=answer.answer, confidence=0.45)
        return AgentDecision(
            action="CHAT" if intent == "UNKNOWN" else intent,
            reply="我可以帮你导航、讲解附近景点，或者回答颐和园历史问题。",
            destination_name=slots.get("destination_name"),
            destination_type=slots.get("destination_type"),
            confidence=0.4,
        )

    async def _explain_nearby(
        self, request: AgentChatRequest, decision: AgentDecision
    ) -> tuple[AgentChatResponse, int | None, str | None]:
        # 视野讲解的数据流：
        # location + heading -> FovService 候选评分 -> 选最高分 POI
        # -> DeepSeek reply 或 MockRAGClient answer -> 返回讲解文本。
        if not request.location or request.heading is None:
            text = decision.reply or "我还不能确定你正在看哪一处建筑，请同步位置和朝向。"
            return self._text_response("EXPLAIN_NEARBY", text), None, None

        candidates = FovService(self.db).get_visible_poi_candidates(request.location, request.heading)
        if not candidates:
            text = decision.reply or "我还不能确定你看的是哪一处建筑，你可以稍微靠近一点，或者把视线对准建筑正面。"
            return self._text_response("EXPLAIN_NEARBY", text), None, None

        poi = candidates[0].poi
        if self.llm.enabled and decision.reply:
            return self._text_response("EXPLAIN_NEARBY", decision.reply), poi.id, "deepseek_chat"

        answer = await self.rag.answer("介绍一下这里", poi_id=poi.id)
        response = AgentChatResponse(
            intent="EXPLAIN_NEARBY",
            response_text=answer.answer,
            tts_text=answer.answer,
            source_chunks=[c.model_dump() for c in answer.chunks],
            suggested_questions=["它为什么有三层？", "慈禧太后在这里看过什么戏？", "样式雷和这座建筑有什么关系？"],
        )
        return response, poi.id, "rag_answer"

    def _text_response(self, intent: str, text: str) -> AgentChatResponse:
        # 把普通文本统一包装成 AgentChatResponse，前端只需要读取
        # response_text/tts_text，不关心后端是不是调用了工具。
        return AgentChatResponse(intent=intent, response_text=text, tts_text=text)
