# RAG 接口测试。
#
# 项目已移除本地预设 RAG。真实 RAG 未接入前，接口应该明确报错，
# 不能再根据 query 返回本地预设回答。


def test_rag_answer_requires_real_backend(client):
    resp = client.post("/api/v1/rag/answer", json={"query": "样式雷是什么？"})
    assert resp.status_code == 501
    assert resp.json()["detail"] == "RAG backend is not configured"
