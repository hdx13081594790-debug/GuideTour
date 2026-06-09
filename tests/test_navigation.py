# 导航接口测试。
#
# 覆盖最近厕所和指定景点路线：
# HTTP 请求 -> NavigationService -> 地图 Provider/LocalGraphRouter -> RouteResponse。

def test_nearest_toilet(client):
    resp = client.post("/api/v1/navigation/nearest", json={
        "session_id": "s001",
        "origin": {"lng": 116.2699, "lat": 39.9991},
        "target_type": "toilet",
        "radius_meters": 1000
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "厕所" in data["destination_name"]
    assert data["distance_meters"] > 0


def test_route_to_deheyuan(client):
    resp = client.post("/api/v1/navigation/route", json={
        "session_id": "s001",
        "origin": {"lng": 116.2699, "lat": 39.9991},
        "destination": {"name": "德和园"},
        "strategy": "walking",
        "language": "zh"
    })
    assert resp.status_code == 200
    assert resp.json()["steps"]
