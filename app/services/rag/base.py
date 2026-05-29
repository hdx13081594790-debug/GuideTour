from abc import ABC, abstractmethod
from app.schemas.rag import RAGAnswer, RAGChunk


class RAGClient(ABC):
    @abstractmethod
    async def retrieve(self, query: str, poi_id: int | None = None, top_k: int = 5, filters: dict | None = None) -> list[RAGChunk]:
        raise NotImplementedError

    @abstractmethod
    async def answer(self, query: str, poi_id: int | None = None, context: dict | None = None) -> RAGAnswer:
        raise NotImplementedError
