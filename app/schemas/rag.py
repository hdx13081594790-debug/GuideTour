from pydantic import BaseModel, Field


class RAGChunk(BaseModel):
    chunk_id: str
    title: str
    content: str
    source: str | None = None
    poi_id: int | None = None
    score: float
    metadata: dict = Field(default_factory=dict)


class RAGAnswer(BaseModel):
    answer: str
    chunks: list[RAGChunk]
    confidence: float
    safety_notes: list[str] = Field(default_factory=list)


class RAGRetrieveRequest(BaseModel):
    query: str
    poi_id: int | None = None
    top_k: int = 5
    filters: dict | None = None


class RAGAnswerRequest(BaseModel):
    query: str
    poi_id: int | None = None
    context: dict | None = None
