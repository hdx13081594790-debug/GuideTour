from fastapi import APIRouter

from app.core.exceptions import AppError
from app.schemas.rag import RAGAnswer, RAGAnswerRequest, RAGChunk, RAGRetrieveRequest

# RAG 路由。
#
# 本项目已移除本地预设 RAG，不再根据 query 返回写死的知识内容。
# 在真实向量数据库/真实 RAG 服务接入前，这两个接口会明确报错。

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/retrieve", response_model=list[RAGChunk])
async def retrieve(_: RAGRetrieveRequest):
    raise AppError("RAG backend is not configured", 501)


@router.post("/answer", response_model=RAGAnswer)
async def answer(_: RAGAnswerRequest):
    raise AppError("RAG backend is not configured", 501)
