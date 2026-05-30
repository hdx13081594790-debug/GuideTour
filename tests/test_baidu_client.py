import pytest

from app.schemas.location import GeoPoint
from app.services.map.baidu_client import BaiduClient


@pytest.mark.anyio
async def test_baidu_search_poi_parses_results():
    client = BaiduClient("test-ak")
    calls = []

    async def fake_get_json(url, params):
        calls.append((url, params))
        return {
            "status": 0,
            "results": [
                {
                    "name": "颐和园卫生间",
                    "address": "北京市海淀区",
                    "area": "海淀区",
                    "location": {"lng": 116.2703, "lat": 39.9988},
                    "detail_info": {"tag": "生活服务"},
                }
            ],
        }

    client._get_json = fake_get_json
    items = await client.search_poi("卫生间", GeoPoint(lng=116.2699, lat=39.9991), radius=500)

    assert items[0].name == "颐和园卫生间"
    assert items[0].location.coord_type == "bd09"
    assert calls[0][1]["location"] == "39.9991,116.2699"
    assert calls[0][1]["radius"] == 500


@pytest.mark.anyio
async def test_baidu_walking_route_parses_steps():
    client = BaiduClient("test-ak")

    async def fake_get_json(url, params):
        return {
            "status": 0,
            "result": {
                "routes": [
                    {
                        "distance": 120,
                        "duration": 100,
                        "steps": [
                            {
                                "instruction": "<b>向东步行</b>约80米",
                                "distance": 80,
                                "duration": 70,
                                "direction": "east",
                                "turn_type": "直行",
                                "path": "116.2700,39.9991;116.2705,39.9992",
                            }
                        ],
                    }
                ]
            },
        }

    client._get_json = fake_get_json
    route = await client.walking_route(
        GeoPoint(lng=116.2699, lat=39.9991),
        GeoPoint(lng=116.2708, lat=39.9993),
        "测试目的地",
    )

    assert route.distance_meters == 120
    assert route.duration_seconds == 100
    assert route.steps[0].instruction == "向东步行约80米"
    assert route.polyline[1].lng == 116.2700
    assert route.destination_name == "测试目的地"
