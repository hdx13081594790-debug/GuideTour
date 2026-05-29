from sqlalchemy.orm import Session
from app.repositories.poi_repo import POIRepository
from app.repositories.session_repo import SessionRepository
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.schemas.common import ActionResult
from app.schemas.navigation import DestinationRef, RouteRequest
from app.schemas.photo import PhotoCaptureRequest
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

    async def chat(self, request: AgentChatRequest) -> AgentChatResponse:
        intent, slots = classify_intent(request.text)
        response: AgentChatResponse
        tool_called = None
        related_poi_id = None

        if intent == "NAVIGATE_NEAREST_SERVICE":
            if not request.location:
                response = AgentChatResponse(intent=intent, response_text="请先同步当前位置，我再帮你规划最近路线。", tts_text="请先同步当前位置，我再帮你规划最近路线。")
            else:
                route = await self.nav.nearest_route(request.session_id, request.location, slots["destination_type"])
                tool_called = "navigation_nearest"
                response = AgentChatResponse(intent=intent, response_text=route.tts_text, tts_text=route.tts_text, route=route, actions=[ActionResult(type="navigation_started", task_id=route.task_id)])
        elif intent == "NAVIGATE_TO_POI":
            destination_name = slots.get("destination_name")
            if not destination_name and request.detected_pois:
                destination_name = request.detected_pois[0].get("name")
            if not request.location or not destination_name:
                response = AgentChatResponse(intent=intent, response_text="我还不确定目的地。你可以说具体景点名，或者把视线对准建筑。", tts_text="我还不确定目的地。")
            else:
                route = await self.nav.plan_route(RouteRequest(session_id=request.session_id, origin=request.location, destination=DestinationRef(name=destination_name)))
                tool_called = "navigation_route"
                response = AgentChatResponse(intent=intent, response_text=route.tts_text, tts_text=route.tts_text, route=route, actions=[ActionResult(type="navigation_started", task_id=route.task_id)])
        elif intent == "EXPLAIN_NEARBY":
            if not request.location or request.heading is None:
                response = AgentChatResponse(intent=intent, response_text="我还不能确定你正在看哪一处建筑，请同步位置和朝向。", tts_text="我还不能确定你正在看哪一处建筑。")
            else:
                candidates = FovService(self.db).get_visible_poi_candidates(request.location, request.heading)
                if not candidates:
                    response = AgentChatResponse(intent=intent, response_text="我还不能确定你看的是哪一处建筑，你可以稍微靠近一点，或者把视线对准建筑正面。", tts_text="我还不能确定你看的是哪一处建筑。")
                else:
                    poi = candidates[0].poi
                    answer = await self.rag.answer("介绍一下这里", poi_id=poi.id)
                    related_poi_id = poi.id
                    tool_called = "rag_answer"
                    response = AgentChatResponse(intent=intent, response_text=answer.answer, tts_text=answer.answer, source_chunks=[c.model_dump() for c in answer.chunks], suggested_questions=["它为什么有三层？", "慈禧太后在这里看过什么戏？", "样式雷和这座建筑有什么关系？"])
        elif intent == "ASK_HISTORY":
            poi_id = request.current_poi_id or (request.detected_pois[0].get("poi_id") if request.detected_pois else None)
            answer = await self.rag.answer(request.text, poi_id=poi_id)
            related_poi_id = poi_id
            tool_called = "rag_answer"
            response = AgentChatResponse(intent=intent, response_text=answer.answer, tts_text=answer.answer, source_chunks=[c.model_dump() for c in answer.chunks])
        elif intent == "TAKE_PHOTO":
            photo = PhotoService(self.db).capture(PhotoCaptureRequest(session_id=request.session_id, device_id=request.device_id))
            tool_called = "photo_capture"
            response = AgentChatResponse(intent=intent, response_text="已拍照，稍后可在纪念册中查看。", tts_text="已拍照，稍后可在纪念册中查看。", actions=[ActionResult(type="photo", status="triggered", message=photo.asset_id)])
        elif intent == "STOP_NAVIGATION":
            task_id = self.nav.stop(request.session_id)
            tool_called = "navigation_stop"
            response = AgentChatResponse(intent=intent, response_text="已停止导航。", tts_text="已停止导航。", actions=[ActionResult(type="navigation_stopped", status="triggered", task_id=task_id)])
        else:
            response = AgentChatResponse(intent=intent, response_text="我可以帮你导航、讲解附近景点，或者回答颐和园历史问题。", tts_text="我可以帮你导航、讲解附近景点，或者回答颐和园历史问题。")

        SessionRepository(self.db).log(request.session_id, request.device_id, "text", request.text, intent, tool_called, response.response_text, related_poi_id)
        return response
