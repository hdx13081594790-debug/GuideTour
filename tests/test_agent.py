# Agent 端到端测试。
#
# 覆盖 /api/v1/agent/chat 的两条核心路径：
# - 导航意图：返回 route/actions；
# - 历史问答：返回 response_text。

def test_agent_navigate_toilet(client):
    resp = client.post("/api/v1/agent/chat", json={
        "session_id": "agent1",
        "device_id": "glass001",
        "text": "我想去最近的厕所",
        "location": {"lng": 116.2699, "lat": 39.9991},
        "heading": 85
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "NAVIGATE_NEAREST_SERVICE"
    assert data["route"]["task_id"].startswith("nav_")


def test_agent_history_question(client):
    resp = client.post("/api/v1/agent/chat", json={
        "session_id": "agent2",
        "text": "这个建筑为什么有三层？",
        "current_poi_id": 2
    })
    assert resp.status_code == 200
    assert "三层" in resp.json()["response_text"]
