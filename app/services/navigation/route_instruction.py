def summarize_route(destination_name: str, distance_meters: float, duration_seconds: int) -> str:
    return f"已为你规划去{destination_name}的步行路线，全程约{int(distance_meters)}米，预计{max(1, round(duration_seconds / 60))}分钟。"
