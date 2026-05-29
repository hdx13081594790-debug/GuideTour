from app.schemas.rag import RAGAnswer, RAGChunk
from app.services.rag.base import RAGClient


class MockRAGClient(RAGClient):
    async def retrieve(self, query: str, poi_id: int | None = None, top_k: int = 5, filters: dict | None = None) -> list[RAGChunk]:
        corpus = [
            RAGChunk(chunk_id="deheyuan_theater", title="德和园大戏楼", content="德和园大戏楼是清代皇家园林中重要的戏曲演出空间，三层戏台可配合机关、升降与声效表现神仙鬼怪、山水变化等复杂场面。", source="mock", poi_id=2, score=0.92),
            RAGChunk(chunk_id="cixi_opera", title="慈禧与听戏", content="德和园常与晚清宫廷听戏活动相关，慈禧太后曾在此观看戏曲演出。讲解时应避免编造具体剧目和日期。", source="mock", poi_id=2, score=0.86),
            RAGChunk(chunk_id="yangshilei", title="样式雷", content="样式雷是清代负责皇家建筑设计的雷氏家族称谓，其图档反映了皇家建筑设计与营造制度。", source="mock", poi_id=None, score=0.82),
            RAGChunk(chunk_id="foxiangge", title="佛香阁", content="佛香阁位于万寿山前山中轴线上，是颐和园标志性建筑之一，登高可俯瞰昆明湖。", source="mock", poi_id=8, score=0.80),
        ]
        query_hit = [c for c in corpus if (poi_id and c.poi_id == poi_id) or any(k in query for k in [c.title, "样式雷", "慈禧", "戏楼", "三层", "佛香阁"] if k)]
        return (query_hit or [])[:top_k]

    async def answer(self, query: str, poi_id: int | None = None, context: dict | None = None) -> RAGAnswer:
        chunks = await self.retrieve(query, poi_id=poi_id)
        if not chunks:
            return RAGAnswer(answer="我暂时没有查到权威资料，先不贸然补充历史细节。你可以换个问法，或把视线对准建筑正面让我再判断一次。", chunks=[], confidence=0.2, safety_notes=["no_authoritative_context"])
        content = "；".join(c.content for c in chunks[:2])
        return RAGAnswer(answer=f"{content} 如果你愿意继续听，我还可以接着讲它的建筑布局和相关人物故事。", chunks=chunks, confidence=max(c.score for c in chunks))
