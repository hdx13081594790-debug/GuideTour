from sqlalchemy.orm import Session

from app.repositories.poi_repo import POIRepository
from app.repositories.session_repo import SessionRepository
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.schemas.common import ActionResult
from app.schemas.navigation import DestinationRef, RouteRequest
from app.schemas.photo import PhotoCaptureRequest
from app.services.agent.deepseek_client import AgentDecision, DeepSeekAgentClient
from app.services.location.fov_service import FovService
from app.services.navigation.navigation_service import NavigationService
from app.services.photo.photo_service import PhotoService

# GuideAgent 是后端 Agent 编排层。
#
# 重要原则：这里不再做任何“按用户字符串规则识别后返回预设答案”的兜底。
# 用户输入必须先交给 DeepSeek；DeepSeek 连不上、没配置 key、返回格式错误，
# 就直接抛错，让接口暴露真实失败原因。
#
# 数据流：
# POST /api/v1/agent/chat
# -> AgentChatRequest
# -> DeepSeekAgentClient.decide()
# -> AgentDecision.action 决定是否调用导航/拍照/停止导航等工具
# -> AgentChatResponse 返回前端。


class GuideAgent:
    def __init__(self, db: Session):
        self.db = db
        self.poi_repo = POIRepository(db)
        self.nav = NavigationService(db)
        self.llm = DeepSeekAgentClient()

    async def chat(self, request: AgentChatRequest) -> AgentChatResponse:
        decision = await self._decide(request)
        intent = decision.action
        tool_called = "deepseek_chat"
        related_poi_id = None

        if intent == "NAVIGATE_NEAREST_SERVICE":
            response = await self._navigate_nearest(request, decision)
            tool_called = "navigation_nearest"

        elif intent == "NAVIGATE_TO_POI":
            response = await self._navigate_to_poi(request, decision)
            tool_called = "navigation_route" if response.route else "deepseek_chat"

        elif intent == "EXPLAIN_NEARBY":
            response, related_poi_id = await self._explain_nearby(request, decision)

        elif intent in {"ASK_HISTORY", "CHAT"}:
            response = self._text_response(intent, decision.reply)
            related_poi_id = request.current_poi_id or (
                request.detected_pois[0].get("poi_id") if request.detected_pois else None
            )

        elif intent == "TAKE_PHOTO":
            photo = PhotoService(self.db).capture(
                PhotoCaptureRequest(session_id=request.session_id, device_id=request.device_id)
            )
            text = "已拍照，稍后可在纪念册中查看。"
            response = AgentChatResponse(
                intent=intent,
                response_text=text,
                tts_text=text,
                actions=[ActionResult(type="photo", status="triggered", message=photo.asset_id)],
            )
            tool_called = "photo_capture"

        elif intent == "STOP_NAVIGATION":
            task_id = self.nav.stop(request.session_id)
            text = "已停止导航。"
            response = AgentChatResponse(
                intent=intent,
                response_text=text,
                tts_text=text,
                actions=[ActionResult(type="navigation_stopped", status="triggered", task_id=task_id)],
            )
            tool_called = "navigation_stop"

        else:
            response = self._text_response("CHAT", decision.reply)

        SessionRepository(self.db).log(
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
        if not self.llm.enabled:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured")
        poi_names = [poi.name for poi in self.poi_repo.search(limit=200)]
        return await self.llm.decide(request, poi_names)

    async def _navigate_nearest(self, request: AgentChatRequest, decision: AgentDecision) -> AgentChatResponse:
        if not request.location:
            raise RuntimeError("Location is required to plan nearest-service navigation")
        destination_type = decision.destination_type
        if not destination_type:
            raise RuntimeError("DeepSeek did not provide destination_type for nearest-service navigation")
        route = await self.nav.nearest_route(request.session_id, request.location, destination_type)
        return AgentChatResponse(
            intent=decision.action,
            response_text=route.tts_text,
            tts_text=route.tts_text,
            route=route,
            actions=[ActionResult(type="navigation_started", task_id=route.task_id)],
        )

    async def _navigate_to_poi(self, request: AgentChatRequest, decision: AgentDecision) -> AgentChatResponse:
        if decision.needs_clarification:
            return self._text_response(decision.action, decision.reply)
        if not request.location:
            raise RuntimeError("Location is required to plan POI navigation")
        if not decision.destination_name:
            raise RuntimeError("DeepSeek did not provide destination_name for POI navigation")
        route = await self.nav.plan_route(
            RouteRequest(
                session_id=request.session_id,
                origin=request.location,
                destination=DestinationRef(name=decision.destination_name),
            )
        )
        return AgentChatResponse(
            intent=decision.action,
            response_text=route.tts_text,
            tts_text=route.tts_text,
            route=route,
            actions=[ActionResult(type="navigation_started", task_id=route.task_id)],
        )

    async def _explain_nearby(
        self, request: AgentChatRequest, decision: AgentDecision
    ) -> tuple[AgentChatResponse, int | None]:
        if not request.location or request.heading is None:
            raise RuntimeError("Location and heading are required for EXPLAIN_NEARBY")
        candidates = FovService(self.db).get_visible_poi_candidates(request.location, request.heading)
        if not candidates:
            raise RuntimeError("No visible POI candidate found for EXPLAIN_NEARBY")
        poi = candidates[0].poi
        return self._text_response("EXPLAIN_NEARBY", decision.reply), poi.id

    def _text_response(self, intent: str, text: str) -> AgentChatResponse:
        if not text:
            raise RuntimeError("DeepSeek did not provide a reply")
        return AgentChatResponse(intent=intent, response_text=text, tts_text=text)
