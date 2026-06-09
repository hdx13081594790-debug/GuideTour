from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.schemas.agent import AgentChatRequest, AgentChatResponse, ExplainNearbyRequest, ExplainNearbyResponse
from app.services.agent.graph import GuideAgent
from app.services.location.fov_service import FovService

# Agent 路由层。
#
# 这里不做规则意图识别，也不返回本地预设问答。
# /chat 和 /explain-nearby 都会进入 GuideAgent，GuideAgent 必须调用 DeepSeek。
# 如果 DeepSeek key 缺失、网络失败或返回格式错误，接口会直接报错。

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def chat(payload: AgentChatRequest, db: Session = Depends(get_db)):
    return await GuideAgent(db).chat(payload)


@router.post("/explain-nearby", response_model=ExplainNearbyResponse)
async def explain_nearby(payload: ExplainNearbyRequest, db: Session = Depends(get_db)):
    if payload.accuracy_meters is not None and payload.accuracy_meters > 20:
        raise AppError("Location accuracy is too low for EXPLAIN_NEARBY", 400)

    candidates = FovService(db).get_visible_poi_candidates(payload.location, payload.heading)
    if not candidates or candidates[0].score < 0.45:
        raise AppError("No confident visible POI candidate found for EXPLAIN_NEARBY", 404)

    poi = candidates[0].poi
    answer = await GuideAgent(db).chat(
        AgentChatRequest(
            session_id=payload.session_id,
            device_id=payload.device_id,
            text="介绍一下这里",
            location=payload.location,
            heading=payload.heading,
            language=payload.language,
            current_poi_id=poi.id,
            detected_pois=[{"poi_id": poi.id, "name": poi.name, "confidence": candidates[0].confidence}],
        )
    )
    return ExplainNearbyResponse(
        poi_id=poi.id,
        poi_name=poi.name,
        confidence=candidates[0].score,
        explanation=answer.response_text,
        suggested_questions=answer.suggested_questions,
        tts_text=answer.tts_text,
    )
