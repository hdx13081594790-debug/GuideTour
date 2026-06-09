from fastapi import APIRouter
from app.schemas.rag import RAGAnswer, RAGAnswerRequest, RAGChunk, RAGRetrieveRequest
from app.services.rag.mock_rag_client import MockRAGClient

# RAG 路由。
#
# MVP 阶段直接调用 MockRAGClient；
# 未来公司向量库接入后，只要新的客户端实现 RAGClient 接口，
# 这里可以很小改动或不改动地替换。

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/retrieve", response_model=list[RAGChunk])
async def retrieve(payload: RAGRetrieveRequest):
    # 返回证据片段，适合调试检索质量。
    return await MockRAGClient().retrieve(payload.query, payload.poi_id, payload.top_k, payload.filters)


@router.post("/answer", response_model=RAGAnswer)
async def answer(payload: RAGAnswerRequest):
    # 返回面向游客的最终回答。
    return await MockRAGClient().answer(payload.query, payload.poi_id, payload.context)
