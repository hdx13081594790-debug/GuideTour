from __future__ import annotations

import re


def detect_language(text: str | None) -> str:
    if not text:
        return "zh"
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    return "en"


def language_label(language: str) -> str:
    return {"zh": "中文", "en": "English", "ja": "日本語"}.get(language, "中文")


def localize(text_zh: str, language: str) -> str:
    if language == "en":
        return (
            "Demo translation: "
            + text_zh.replace("颐和园", "the Summer Palace").replace("佛香阁", "Tower of Buddhist Incense")
        )
    if language == "ja":
        return "デモ翻訳：" + text_zh
    return text_zh
