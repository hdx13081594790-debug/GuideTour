from app.services.rag.mock_rag_client import MockRAGClient

# VectorRAGClient 是真实向量数据库客户端的占位类。
#
# 当前继承 MockRAGClient 是为了让接口先可用。
# 后续接公司向量库时，应在这里实现：
# - retrieve(): 调向量库 top_k 检索；
# - answer(): 将检索 chunks 交给大模型生成回答。


class VectorRAGClient(MockRAGClient):
    """Placeholder for the company-provided vector database client."""
