# 位置状态测试。
#
# 覆盖 /location/update 和 /location/current：
# 上传设备位置 -> Redis/内存位置仓库保存 -> 按 session 读取。

def test_location_update_and_current(client):
    payload = {
        "session_id": "loc1",
        "device_id": "glass001",
        "location": {"lng": 116.2699, "lat": 39.9991},
        "heading": 85,
        "pitch": 0,
        "roll": 0,
        "accuracy_meters": 5,
    }
    update_resp = client.post("/api/v1/location/update", json=payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["location"]["lng"] == 116.2699

    current_resp = client.get("/api/v1/location/current/loc1")
    assert current_resp.status_code == 200
    data = current_resp.json()
    assert data["session_id"] == "loc1"
    assert data["device_id"] == "glass001"
    assert data["heading"] == 85
