# 导航文案小工具。
#
# 目前只有路线总览 TTS 拼接。后续如果要根据儿童/老人/外语等风格
# 生成不同播报文案，可以把规则集中扩展在这里。

def summarize_route(destination_name: str, distance_meters: float, duration_seconds: int) -> str:
    return f"已为你规划去{destination_name}的步行路线，全程约{int(distance_meters)}米，预计{max(1, round(duration_seconds / 60))}分钟。"
