from abc import ABC, abstractmethod
from app.schemas.rag import RAGAnswer, RAGChunk

# RAGClient 抽象接口。
#
# Agent 和 RAG 路由只依赖这个接口，不关心底层是 Mock、向量数据库、
# 还是公司后续提供的知识检索服务。
#
# retrieve：只拿证据片段；
# answer：基于证据生成面向游客的回答。


class RAGClient(ABC):
    @abstractmethod
    async def retrieve(self, query: str, poi_id: int | None = None, top_k: int = 5, filters: dict | None = None) -> list[RAGChunk]:
        raise NotImplementedError

    @abstractmethod
    async def answer(self, query: str, poi_id: int | None = None, context: dict | None = None) -> RAGAnswer:
        raise NotImplementedError
