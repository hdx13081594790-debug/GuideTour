# WebSocket 测试。
#
# 覆盖实时推送链路：
# 客户端连接 /ws/{session_id}
# -> HTTP 更新位置
# -> connection_manager.broadcast
# -> WebSocket 收到 location_updated。

def test_websocket_receives_location_update(client):
    with client.websocket_connect("/api/v1/ws/ws-location-1") as websocket:
        connected = websocket.receive_json()
        assert connected["type"] == "connected"

        resp = client.post("/api/v1/location/update", json={
            "session_id": "ws-location-1",
            "device_id": "glass001",
            "location": {"lng": 116.2699, "lat": 39.9991},
            "heading": 85,
            "accuracy_meters": 5,
        })
        assert resp.status_code == 200

        event = websocket.receive_json()
        assert event["type"] == "location_updated"
        assert event["session_id"] == "ws-location-1"
        assert event["location"]["location"]["lng"] == 116.2699


def test_websocket_receives_navigation_events(client):
    with client.websocket_connect("/api/v1/ws/ws-nav-1") as websocket:
        assert websocket.receive_json()["type"] == "connected"

        route_resp = client.post("/api/v1/navigation/nearest", json={
            "session_id": "ws-nav-1",
            "origin": {"lng": 116.2699, "lat": 39.9991},
            "target_type": "toilet",
            "radius_meters": 1000,
        })
        assert route_resp.status_code == 200
        task_id = route_resp.json()["task_id"]

        started = websocket.receive_json()
        assert started["type"] == "navigation_started"
        assert started["task_id"] == task_id
        assert started["state"]["status"] == "navigating"

        update_resp = client.post("/api/v1/navigation/update-position", json={
            "session_id": "ws-nav-1",
            "task_id": task_id,
            "location": {"lng": 116.2700, "lat": 39.9990},
            "heading": 90,
        })
        assert update_resp.status_code == 200

        updated = websocket.receive_json()
        assert updated["type"] == "navigation_updated"
        assert updated["task_id"] == task_id
        assert updated["state"]["last_location"]["lng"] == 116.2700
