from fastapi import APIRouter
from app.schemas.rag import RAGAnswer, RAGAnswerRequest, RAGChunk, RAGRetrieveRequest
from app.services.rag.mock_rag_client import MockRAGClient

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/retrieve", response_model=list[RAGChunk])
async def retrieve(payload: RAGRetrieveRequest):
    return await MockRAGClient().retrieve(payload.query, payload.poi_id, payload.top_k, payload.filters)


@router.post("/answer", response_model=RAGAnswer)
async def answer(payload: RAGAnswerRequest):
    return await MockRAGClient().answer(payload.query, payload.poi_id, payload.context)
