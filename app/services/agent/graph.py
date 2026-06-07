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


class GuideAgent:
    def __init__(self, db: Session):
        self.db = db
        self.poi_repo = POIRepository(db)
        self.nav = NavigationService(db)
        self.rag = MockRAGClient()
        self.llm = DeepSeekAgentClient()

    async def chat(self, request: AgentChatRequest) -> AgentChatResponse:
        decision = await self._decide(request)
        intent = decision.action
        tool_called = None
        related_poi_id = None

        if intent == "NAVIGATE_NEAREST_SERVICE":
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
            response, related_poi_id, tool_called = await self._explain_nearby(request, decision)

        elif intent in {"ASK_HISTORY", "CHAT"}:
            related_poi_id = request.current_poi_id or (
                request.detected_pois[0].get("poi_id") if request.detected_pois else None
            )
            tool_called = "deepseek_chat" if self.llm.enabled else "rule_chat"
            text = decision.reply or "我可以继续回答你的问题，也可以帮你规划路线。"
            response = self._text_response(intent, text)

        elif intent == "TAKE_PHOTO":
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
        if self.llm.enabled:
            try:
                poi_names = [poi.name for poi in self.poi_repo.search(limit=200)]
                return await self.llm.decide(request, poi_names)
            except Exception:
                if not self.llm.settings.deepseek_fallback_to_rules:
                    raise

        intent, slots = classify_intent(request.text)
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
        return AgentChatResponse(intent=intent, response_text=text, tts_text=text)
