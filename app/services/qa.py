from __future__ import annotations

import re

from app import repository
from app.services.language import detect_language, localize


def classify_intent(message: str) -> str:
    text = message.lower()
    if any(token in text for token in ["路线", "route", "行程", "怎么走", "recommend"]):
        return "route"
    if any(token in text for token in ["识别", "照片", "image", "photo", "拍"]):
        return "vision"
    return "qa"


def _tokens(text: str) -> set[str]:
    chinese = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    latin = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return set(chinese + latin)


def search_knowledge(message: str, current_poi_id: str | None = None) -> list[dict]:
    docs = repository.list_docs()
    query_tokens = _tokens(message)
    scored = []
    for doc in docs:
        score = 0
        haystack = f"{doc['title']} {doc['content']} {' '.join(doc['tags'])}"
        for token in query_tokens:
            if token in haystack.lower() or token in haystack:
                score += 2
        if current_poi_id and doc["poi_id"] == current_poi_id:
            score += 3
        for poi in repository.list_pois():
            if poi["name"] in message and doc["poi_id"] == poi["id"]:
                score += 5
        if score:
            scored.append((score, doc))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:3]]


def answer_question(message: str, language: str | None, current_poi_id: str | None) -> tuple[str, list[dict], list[dict], str]:
    language = language or detect_language(message)
    intent = classify_intent(message)
    docs = search_knowledge(message, current_poi_id)
    pois = repository.list_pois()
    matched_poi = next((poi for poi in pois if poi["name"] in message or poi["name_en"].lower() in message.lower()), None)

    if intent == "route":
        answer = "可以。我建议先选择起点、游览时长和兴趣标签，然后生成一条 POI 路线。当前 demo 支持历史、建筑、湖景、摄影、亲子等偏好。"
        actions = [{"type": "open_route", "label": "生成路线"}]
    elif matched_poi:
        answer = f"{matched_poi['name']}：{matched_poi['summary']} {matched_poi['story']}"
        actions = [{"type": "set_current_poi", "poi_id": matched_poi["id"], "label": f"设为当前景点"}]
    elif docs:
        answer = docs[0]["content"]
        actions = [{"type": "ask_followup", "label": "继续追问历史故事"}]
    else:
        answer = "这个问题我在当前知识库里还没有可靠依据。你可以换成景点介绍、路线推荐、拍照识别或开放游览建议。"
        actions = [{"type": "fallback", "label": "查看推荐问题"}]

    citations = [{"id": doc["id"], "title": doc["title"], "poi_id": doc["poi_id"]} for doc in docs]
    return localize(answer, language), citations, actions, intent
