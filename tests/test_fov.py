# 视野讲解测试。
#
# explain-nearby 现在也必须走 DeepSeek。测试通过 monkeypatch 模拟模型返回，
# 只验证“位置 + 朝向 -> FovService 候选 POI -> DeepSeek 回答”这条链路。

from app.services.agent.deepseek_client import AgentDecision, DeepSeekAgentClient


def test_explain_nearby(client, monkeypatch):
    async def fake_decide(self, request, poi_names):
        return AgentDecision(
            action="EXPLAIN_NEARBY",
            reply="你现在看到的是德和园大戏楼。",
            confidence=0.98,
        )

    monkeypatch.setattr(DeepSeekAgentClient, "decide", fake_decide)

    resp = client.post("/api/v1/agent/explain-nearby", json={
        "session_id": "s001",
        "device_id": "glass001",
        "location": {"lng": 116.2728, "lat": 39.99955},
        "heading": 90,
        "language": "zh",
        "style": "normal",
        "accuracy_meters": 5,
    })
    assert resp.status_code == 200
    assert resp.json()["poi_id"] is not None
    assert "德和园" in resp.json()["explanation"]


def test_explain_bad_accuracy(client):
    resp = client.post("/api/v1/agent/explain-nearby", json={
        "session_id": "s001",
        "location": {"lng": 116.2728, "lat": 39.99955},
        "heading": 90,
        "accuracy_meters": 80,
    })
    assert resp.status_code == 400
