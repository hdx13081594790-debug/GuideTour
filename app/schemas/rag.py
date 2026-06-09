from pydantic import BaseModel, Field

# RAG 接口数据契约。
#
# retrieve 阶段返回 RAGChunk 证据片段；
# answer 阶段返回 RAGAnswer，包含最终回答、引用片段和置信度。
# 当前项目不再提供本地预设 RAG。未来真实向量库接入后，
# 仍应返回同样结构，方便前端和 Agent 复用。


class RAGChunk(BaseModel):
    # 一段可引用的知识片段。
    chunk_id: str
    title: str
    content: str
    source: str | None = None
    poi_id: int | None = None
    score: float
    metadata: dict = Field(default_factory=dict)


class RAGAnswer(BaseModel):
    # 面向用户的最终答案 + 支撑答案的 chunks。
    answer: str
    chunks: list[RAGChunk]
    confidence: float
    safety_notes: list[str] = Field(default_factory=list)


class RAGRetrieveRequest(BaseModel):
    # 检索请求，可按 poi_id 和 filters 限定范围。
    query: str
    poi_id: int | None = None
    top_k: int = 5
    filters: dict | None = None


class RAGAnswerRequest(BaseModel):
    # 问答请求，context 可传讲解风格、当前视野等额外上下文。
    query: str
    poi_id: int | None = None
    context: dict | None = None
