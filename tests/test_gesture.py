def test_gesture_take_photo(client):
    resp = client.post("/api/v1/vision/analyze-frames", json={
        "session_id": "gesture1",
        "device_id": "glass001",
        "frame_ids": ["f1"],
        "mock_gesture": "take_photo"
    })
    assert resp.status_code == 200
    assert resp.json()["actions"][0]["type"] == "photo"
