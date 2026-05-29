def classify_intent(text: str) -> tuple[str, dict]:
    normalized = text.strip()
    slots: dict = {}
    if any(word in normalized for word in ["停止导航", "取消导航", "别导航"]):
        return "STOP_NAVIGATION", slots
    if any(word in normalized for word in ["拍照", "照相"]):
        return "TAKE_PHOTO", slots
    if any(word in normalized for word in ["厕所", "卫生间", "洗手间"]):
        slots["destination_type"] = "toilet"
        return "NAVIGATE_NEAREST_SERVICE", slots
    for service_word, poi_type in [("出口", "exit"), ("入口", "entrance"), ("医疗", "medical"), ("服务中心", "service_center")]:
        if service_word in normalized and any(v in normalized for v in ["去", "最近", "带我"]):
            slots["destination_type"] = poi_type
            return "NAVIGATE_NEAREST_SERVICE", slots
    if any(word in normalized for word in ["介绍", "讲讲", "这里", "这个建筑是什么"]):
        return "EXPLAIN_NEARBY", slots
    if any(word in normalized for word in ["为什么", "历史", "慈禧", "样式雷", "三层", "故事"]):
        return "ASK_HISTORY", slots
    if any(word in normalized for word in ["去", "怎么走", "带我", "我要到", "我要去"]):
        for name in ["德和园大戏楼", "德和园", "仁寿殿", "仁寿门", "苏州街", "谐趣园", "长廊", "佛香阁", "昆明湖", "排云殿", "大戏楼"]:
            if name in normalized:
                slots["destination_name"] = "德和园大戏楼" if name == "大戏楼" else name
                break
        return "NAVIGATE_TO_POI", slots
    return "UNKNOWN", slots
