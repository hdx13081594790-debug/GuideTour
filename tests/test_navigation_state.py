from app.services.navigation.state_store import navigation_state_store

# 导航实时状态测试。
#
# 覆盖路线创建、位置更新、停止导航后 Redis/内存状态是否同步变化。


def test_navigation_state_saved_updated_and_cancelled(client):
    route_resp = client.post("/api/v1/navigation/nearest", json={
        "session_id": "nav-state-1",
        "origin": {"lng": 116.2699, "lat": 39.9991},
        "target_type": "toilet",
        "radius_meters": 1000,
    })
    assert route_resp.status_code == 200
    route = route_resp.json()
    task_id = route["task_id"]

    state = navigation_state_store.get(task_id)
    assert state is not None
    assert state.session_id == "nav-state-1"
    assert state.status == "navigating"
    assert state.distance_to_destination_meters == route["distance_meters"]
    assert navigation_state_store.active_for_session("nav-state-1").task_id == task_id

    update_resp = client.post("/api/v1/navigation/update-position", json={
        "session_id": "nav-state-1",
        "task_id": task_id,
        "location": {"lng": 116.2701, "lat": 39.9990},
        "heading": 90,
    })
    assert update_resp.status_code == 200
    updated = navigation_state_store.get(task_id)
    assert updated.last_location.lng == 116.2701
    assert updated.last_instruction == update_resp.json()["instruction"]

    state_resp = client.get(f"/api/v1/navigation/{task_id}/state")
    assert state_resp.status_code == 200
    assert state_resp.json()["task_id"] == task_id

    stop_resp = client.post("/api/v1/navigation/stop", json={"session_id": "nav-state-1", "task_id": task_id})
    assert stop_resp.status_code == 200
    stopped = navigation_state_store.get(task_id)
    assert stopped.status == "cancelled"
    assert navigation_state_store.active_for_session("nav-state-1") is None


def test_navigation_update_advances_step(client):
    route_resp = client.post("/api/v1/navigation/nearest", json={
        "session_id": "nav-step-1",
        "origin": {"lng": 116.2699, "lat": 39.9991},
        "target_type": "toilet",
        "radius_meters": 1000,
    })
    route = route_resp.json()
    task_id = route["task_id"]
    destination = route["polyline"][-1]

    update_resp = client.post("/api/v1/navigation/update-position", json={
        "session_id": "nav-step-1",
        "task_id": task_id,
        "location": destination,
        "heading": 90,
    })

    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["status"] == "arrived"
    assert data["current_step_index"] >= 1
    assert data["distance_to_destination_meters"] < 25


def test_navigation_update_confirms_off_route_after_three_times(client):
    route_resp = client.post("/api/v1/navigation/nearest", json={
        "session_id": "nav-off-route-1",
        "origin": {"lng": 116.2699, "lat": 39.9991},
        "target_type": "toilet",
        "radius_meters": 1000,
    })
    task_id = route_resp.json()["task_id"]
    far_location = {"lng": 116.2900, "lat": 40.0100}

    first = client.post("/api/v1/navigation/update-position", json={
        "session_id": "nav-off-route-1",
        "task_id": task_id,
        "location": far_location,
        "heading": 90,
    })
    second = client.post("/api/v1/navigation/update-position", json={
        "session_id": "nav-off-route-1",
        "task_id": task_id,
        "location": far_location,
        "heading": 90,
    })
    third = client.post("/api/v1/navigation/update-position", json={
        "session_id": "nav-off-route-1",
        "task_id": task_id,
        "location": far_location,
        "heading": 90,
    })

    assert first.json()["off_route"] is False
    assert second.json()["off_route"] is False
    assert third.json()["off_route"] is True
    assert "偏离" in third.json()["instruction"]
    assert navigation_state_store.get(task_id).off_route_count == 3
