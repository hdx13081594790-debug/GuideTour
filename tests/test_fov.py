def test_explain_nearby(client):
    resp = client.post("/api/v1/agent/explain-nearby", json={
        "session_id": "s001",
        "device_id": "glass001",
        "location": {"lng": 116.2728, "lat": 39.99955},
        "heading": 90,
        "language": "zh",
        "style": "normal",
        "accuracy_meters": 5
    })
    assert resp.status_code == 200
    assert resp.json()["poi_id"] is not None


def test_explain_bad_accuracy(client):
    resp = client.post("/api/v1/agent/explain-nearby", json={
        "session_id": "s001",
        "location": {"lng": 116.2728, "lat": 39.99955},
        "heading": 90,
        "accuracy_meters": 80
    })
    assert resp.status_code == 200
    assert resp.json()["confidence"] == 0
