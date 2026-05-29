from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.agent import AgentChatRequest, AgentChatResponse, ExplainNearbyRequest, ExplainNearbyResponse
from app.services.agent.graph import GuideAgent
from app.services.location.fov_service import FovService
from app.services.rag.mock_rag_client import MockRAGClient

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def chat(payload: AgentChatRequest, db: Session = Depends(get_db)):
    return await GuideAgent(db).chat(payload)


@router.post("/explain-nearby", response_model=ExplainNearbyResponse)
async def explain_nearby(payload: ExplainNearbyRequest, db: Session = Depends(get_db)):
    if payload.accuracy_meters is not None and payload.accuracy_meters > 20:
        text = "当前定位不太稳定，我先不自动讲解，避免认错景点。"
        return ExplainNearbyResponse(confidence=0, explanation=text, suggested_questions=[], tts_text=text)
    candidates = FovService(db).get_visible_poi_candidates(payload.location, payload.heading)
    if not candidates or candidates[0].score < 0.45:
        text = "我还不能确定你看的是哪一处建筑，你可以稍微靠近一点，或者把视线对准建筑正面。"
        return ExplainNearbyResponse(confidence=0.2, explanation=text, suggested_questions=[], tts_text=text)
    poi = candidates[0].poi
    answer = await MockRAGClient().answer("介绍一下这里", poi_id=poi.id, context={"style": payload.style})
    return ExplainNearbyResponse(
        poi_id=poi.id,
        poi_name=poi.name,
        confidence=candidates[0].score,
        explanation=answer.answer,
        suggested_questions=["它为什么有三层？", "慈禧太后在这里看过什么戏？", "样式雷和这座建筑有什么关系？"],
        tts_text=answer.answer,
    )
