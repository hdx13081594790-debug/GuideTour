# RAG 接口测试。
#
# 覆盖 /rag/answer，确认 MockRAGClient 能根据 query 返回有置信度的回答。

def test_rag_answer(client):
    resp = client.post("/api/v1/rag/answer", json={"query": "样式雷是什么？"})
    assert resp.status_code == 200
    assert resp.json()["confidence"] > 0
