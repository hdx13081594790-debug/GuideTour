import math
from app.schemas.location import GeoPoint


def to_amap_point(point: GeoPoint) -> str:
    return f"{point.lng},{point.lat}"


def to_baidu_point(point: GeoPoint) -> str:
    return f"{point.lat},{point.lng}"


def haversine_meters(a: GeoPoint, b: GeoPoint) -> float:
    radius = 6371000
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = math.radians(b.lat - a.lat)
    dlng = math.radians(b.lng - a.lng)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def bearing_degree(a: GeoPoint, b: GeoPoint) -> float:
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlng = math.radians(b.lng - a.lng)
    y = math.sin(dlng) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlng)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def angle_delta(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def meters_per_lng_at_lat(lat: float) -> float:
    return 111320 * math.cos(math.radians(lat))


def point_to_segment_distance_meters(point: GeoPoint, start: GeoPoint, end: GeoPoint) -> float:
    origin_lat = point.lat
    meter_lng = meters_per_lng_at_lat(origin_lat)
    px, py = point.lng * meter_lng, point.lat * 111320
    sx, sy = start.lng * meter_lng, start.lat * 111320
    ex, ey = end.lng * meter_lng, end.lat * 111320
    dx, dy = ex - sx, ey - sy
    if dx == 0 and dy == 0:
        return haversine_meters(point, start)
    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)))
    nearest_x, nearest_y = sx + t * dx, sy + t * dy
    return math.hypot(px - nearest_x, py - nearest_y)


def distance_to_polyline_meters(point: GeoPoint, polyline: list[GeoPoint]) -> float:
    if not polyline:
        return 0
    if len(polyline) == 1:
        return haversine_meters(point, polyline[0])
    return min(point_to_segment_distance_meters(point, polyline[i], polyline[i + 1]) for i in range(len(polyline) - 1))
