# Agent 端到端测试。
#
# 业务代码已经移除规则兜底；测试里显式 monkeypatch DeepSeek 客户端，
# 只模拟外部大模型返回结构化决策，不在项目代码中保留预设字符串回答。

from app.services.agent.deepseek_client import AgentDecision, DeepSeekAgentClient


def test_agent_navigate_toilet(client, monkeypatch):
    async def fake_decide(self, request, poi_names):
        return AgentDecision(
            action="NAVIGATE_NEAREST_SERVICE",
            reply="",
            destination_type="toilet",
            confidence=0.99,
        )

    monkeypatch.setattr(DeepSeekAgentClient, "decide", fake_decide)

    resp = client.post("/api/v1/agent/chat", json={
        "session_id": "agent1",
        "device_id": "glass001",
        "text": "我想去最近的厕所",
        "location": {"lng": 116.2699, "lat": 39.9991},
        "heading": 85,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "NAVIGATE_NEAREST_SERVICE"
    assert data["route"]["task_id"].startswith("nav_")


def test_agent_history_question(client, monkeypatch):
    async def fake_decide(self, request, poi_names):
        return AgentDecision(
            action="ASK_HISTORY",
            reply="德和园大戏楼的三层戏台用于表现更复杂的戏曲场景。",
            confidence=0.99,
        )

    monkeypatch.setattr(DeepSeekAgentClient, "decide", fake_decide)

    resp = client.post("/api/v1/agent/chat", json={
        "session_id": "agent2",
        "text": "这个建筑为什么有三层？",
        "current_poi_id": 2,
    })
    assert resp.status_code == 200
    assert "三层" in resp.json()["response_text"]
