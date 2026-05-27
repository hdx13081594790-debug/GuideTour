from __future__ import annotations

import hashlib
from pathlib import Path

from app import repository
from app.services.language import localize


def recognize_image(filename: str, content: bytes, language: str = "zh", current_poi_id: str | None = None) -> dict:
    pois = repository.list_pois()
    normalized = filename.lower()

    matched = []
    for poi in pois:
        aliases = [poi["id"].lower(), poi["name"].lower(), poi["name_en"].lower()]
        if any(alias and alias in normalized for alias in aliases):
            matched.append((0.88, poi))

    if current_poi_id:
        poi = repository.get_poi(current_poi_id)
        if poi:
            matched.append((0.72, poi))

    if not matched:
        digest = hashlib.sha256(content[:4096] + Path(filename).name.encode()).digest()
        index = digest[0] % len(pois)
        confidence = 0.42 + (digest[1] % 25) / 100
        matched.append((round(confidence, 2), pois[index]))
        matched.append((0.38, pois[(index + 3) % len(pois)]))

    dedup: dict[str, tuple[float, dict]] = {}
    for confidence, poi in matched:
        old = dedup.get(poi["id"])
        if not old or confidence > old[0]:
            dedup[poi["id"]] = (confidence, poi)

    candidates = [
        {
            "poi_id": poi["id"],
            "name": poi["name"],
            "confidence": confidence,
            "summary": poi["summary"],
        }
        for confidence, poi in sorted(dedup.values(), key=lambda item: item[0], reverse=True)[:3]
    ]
    top = candidates[0]
    if top["confidence"] >= 0.7:
        explanation = f"识别结果倾向于 {top['name']}。{top['summary']}"
    else:
        explanation = f"当前图片置信度偏低，最接近的是 {top['name']}。建议换一个更正面的角度再拍。{top['summary']}"

    return {
        "language": language,
        "candidates": candidates,
        "explanation": localize(explanation, language),
        "suggested_questions": [
            f"{top['name']}有什么历史故事？",
            f"从这里下一站去哪里合适？",
            f"{top['name']}适合拍照吗？",
        ],
    }
