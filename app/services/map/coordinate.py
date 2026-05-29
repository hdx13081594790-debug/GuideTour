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
