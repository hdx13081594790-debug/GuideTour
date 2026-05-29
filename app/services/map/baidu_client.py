import re
from uuid import uuid4

import httpx

from app.schemas.location import GeoPoint
from app.schemas.navigation import RouteResponse, RouteStep
from app.schemas.poi import POIRead
from app.services.map.base import MapProviderClient
from app.services.map.coordinate import to_baidu_point
from app.services.map.local_graph_router import LocalGraphRouter


class BaiduClient(MapProviderClient):
    name = "baidu"
    place_search_url = "https://api.map.baidu.com/place/v2/search"
    walking_route_url = "https://api.map.baidu.com/directionlite/v1/walking"
    reverse_geocode_url = "https://api.map.baidu.com/reverse_geocoding/v3/"

    def __init__(self, ak: str | None = None):
        self.ak = ak
        self.fallback = LocalGraphRouter()

    async def search_poi(self, query: str, location: GeoPoint | None = None, radius: int = 1000) -> list[POIRead]:
        if not self.ak:
            return []
        params: dict[str, str | int] = {
            "query": query,
            "output": "json",
            "ak": self.ak,
            "scope": 2,
            "region": "北京市",
        }
        if location:
            params["location"] = to_baidu_point(location)
            params["radius"] = radius
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.get(self.place_search_url, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            return []
        if payload.get("status") not in {0, "0"}:
            return []
        items: list[POIRead] = []
        for index, item in enumerate(payload.get("results", []), start=1):
            loc = item.get("location") or {}
            if "lng" not in loc or "lat" not in loc:
                continue
            detail = item.get("detail_info") or {}
            items.append(
                POIRead(
                    id=-index,
                    name=item.get("name") or query,
                    alias_names=[],
                    poi_type=detail.get("tag") or "map_poi",
                    description=item.get("address") or "",
                    location=GeoPoint(lng=float(loc["lng"]), lat=float(loc["lat"]), coord_type="bd09"),
                    priority=3,
                    area_name=item.get("area"),
                    is_accessible=True,
                    opening_status="unknown",
                )
            )
        return items

    async def walking_route(self, origin: GeoPoint, destination: GeoPoint, destination_name: str = "目的地") -> RouteResponse:
        if not self.ak:
            return await self.fallback.walking_route(origin, destination, destination_name)
        params = {
            "origin": to_baidu_point(origin),
            "destination": to_baidu_point(destination),
            "ak": self.ak,
        }
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.get(self.walking_route_url, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            return await self.fallback.walking_route(origin, destination, destination_name)
        if payload.get("status") not in {0, "0"}:
            return await self.fallback.walking_route(origin, destination, destination_name)
        routes = (payload.get("result") or {}).get("routes") or []
        if not routes:
            return await self.fallback.walking_route(origin, destination, destination_name)

        route = routes[0]
        steps: list[RouteStep] = []
        polyline: list[GeoPoint] = [origin]
        for index, item in enumerate(route.get("steps") or []):
            instruction = _strip_html(item.get("instruction") or f"继续前往{destination_name}")
            steps.append(
                RouteStep(
                    index=index,
                    instruction=instruction,
                    distance_meters=float(item.get("distance") or 0),
                    duration_seconds=int(item.get("duration") or 0),
                    direction=item.get("direction") or "forward",
                    action=item.get("turn_type") or "walk",
                )
            )
            path = item.get("path")
            if path:
                polyline.extend(_parse_baidu_path(path))
        if len(polyline) == 1:
            polyline.append(destination)
        elif polyline[-1].lng != destination.lng or polyline[-1].lat != destination.lat:
            polyline.append(destination)

        distance = float(route.get("distance") or sum(step.distance_meters for step in steps))
        duration = int(route.get("duration") or sum(step.duration_seconds for step in steps))
        if not steps:
            fallback = await self.fallback.walking_route(origin, destination, destination_name)
            steps = fallback.steps
        return RouteResponse(
            task_id=f"nav_{uuid4().hex[:10]}",
            destination_name=destination_name,
            distance_meters=round(distance, 1),
            duration_seconds=duration,
            polyline=polyline,
            steps=steps,
            tts_text=f"已为你规划去{destination_name}的步行路线，全程约{int(distance)}米，预计{max(1, round(duration / 60))}分钟。请按导航提示步行。",
        )

    async def reverse_geocode(self, location: GeoPoint) -> str:
        if not self.ak:
            return await self.fallback.reverse_geocode(location)
        params = {
            "ak": self.ak,
            "output": "json",
            "coordtype": "bd09ll",
            "location": to_baidu_point(location),
            "pois": 1,
        }
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.get(self.reverse_geocode_url, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            return await self.fallback.reverse_geocode(location)
        if payload.get("status") not in {0, "0"}:
            return await self.fallback.reverse_geocode(location)
        result = payload.get("result") or {}
        return result.get("formatted_address") or result.get("business") or await self.fallback.reverse_geocode(location)


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _parse_baidu_path(path: str) -> list[GeoPoint]:
    points: list[GeoPoint] = []
    for raw in path.split(";"):
        parts = raw.split(",")
        if len(parts) != 2:
            continue
        try:
            points.append(GeoPoint(lng=float(parts[0]), lat=float(parts[1]), coord_type="bd09"))
        except ValueError:
            continue
    return points
