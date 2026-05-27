from __future__ import annotations

import heapq
from collections import defaultdict

from app import repository


def _shortest_path(start: str, end: str, edges: list[dict]) -> tuple[list[str], int, int]:
    graph: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
    for edge in edges:
        graph[edge["from_poi_id"]].append((edge["to_poi_id"], edge["walk_minutes"], edge["distance_m"]))

    heap = [(0, 0, start, [start])]
    seen: set[str] = set()
    while heap:
        minutes, distance, node, path = heapq.heappop(heap)
        if node == end:
            return path, minutes, distance
        if node in seen:
            continue
        seen.add(node)
        for nxt, walk, dist in graph[node]:
            if nxt not in seen:
                heapq.heappush(heap, (minutes + walk, distance + dist, nxt, path + [nxt]))
    return [start, end], 0, 0


def recommend_route(start_poi_id: str, duration_minutes: int, interests: list[str], end_poi_id: str | None = None) -> dict:
    pois = {poi["id"]: poi for poi in repository.list_pois()}
    if start_poi_id not in pois:
        raise ValueError("起点不存在，请先选择一个已录入的 POI。")
    if end_poi_id and end_poi_id not in pois:
        raise ValueError("终点不存在，请检查 POI 配置。")

    interests_set = set(interests)
    edges = repository.list_edges()
    stops = [start_poi_id]
    leg_walks: dict[tuple[str, str], int] = {}
    leg_distances: dict[tuple[str, str], int] = {}
    total_walk = 0
    total_distance = 0
    used_minutes = pois[start_poi_id]["visit_minutes"]

    candidates = [poi for poi in pois.values() if poi["id"] != start_poi_id]
    if end_poi_id:
        candidates = [poi for poi in candidates if poi["id"] != end_poi_id]

    def score(poi: dict) -> tuple[int, int]:
        tag_score = len(interests_set.intersection(poi["tags"]))
        classic_bonus = 1 if "经典" in poi["tags"] or "地标" in poi["tags"] else 0
        return (tag_score + classic_bonus, -poi["visit_minutes"])

    for poi in sorted(candidates, key=score, reverse=True):
        current = stops[-1]
        _, walk, distance = _shortest_path(current, poi["id"], edges)
        extra = walk + poi["visit_minutes"]
        if used_minutes + extra <= duration_minutes and poi["id"] not in stops:
            stops.append(poi["id"])
            leg_walks[(current, poi["id"])] = walk
            leg_distances[(current, poi["id"])] = distance
            total_walk += walk
            total_distance += distance
            used_minutes += extra

    if end_poi_id and stops[-1] != end_poi_id:
        current = stops[-1]
        path, walk, distance = _shortest_path(current, end_poi_id, edges)
        extra = walk + pois[end_poi_id]["visit_minutes"]
        if path[-1] == end_poi_id and used_minutes + extra <= duration_minutes:
            stops.append(end_poi_id)
            leg_walks[(current, end_poi_id)] = walk
            leg_distances[(current, end_poi_id)] = distance
            total_walk += walk
            total_distance += distance
            used_minutes += extra

    arrival = 0
    route_stops = []
    previous = None
    for poi_id in stops:
        poi = pois[poi_id]
        if previous:
            walk = leg_walks.get((previous, poi_id), _shortest_path(previous, poi_id, edges)[1])
            arrival += walk
        route_stops.append(
            {
                "poi_id": poi_id,
                "name": poi["name"],
                "arrive_after_minutes": arrival,
                "stay_minutes": poi["visit_minutes"],
                "summary": poi["summary"],
                "tags": poi["tags"],
            }
        )
        arrival += poi["visit_minutes"]
        previous = poi_id

    total_minutes = sum(item["stay_minutes"] for item in route_stops) + total_walk
    names = " → ".join(item["name"] for item in route_stops)
    return {
        "route_id": f"route-{start_poi_id}-{duration_minutes}",
        "total_minutes": total_minutes,
        "total_distance_m": total_distance,
        "stops": route_stops,
        "narrative": f"建议路线：{names}。预计 {total_minutes} 分钟，步行约 {total_distance} 米。",
    }
