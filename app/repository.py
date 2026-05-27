from __future__ import annotations

import json

from app.database import connect, row_to_doc, row_to_poi


def list_pois() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM poi ORDER BY name").fetchall()
    return [row_to_poi(row) for row in rows]


def get_poi(poi_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM poi WHERE id = ?", (poi_id,)).fetchone()
    return row_to_poi(row) if row else None


def upsert_poi(poi: dict) -> dict:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO poi VALUES (:id, :name, :name_en, :x, :y, :tags,
            :open_time, :visit_minutes, :image_url, :summary, :story)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                name_en=excluded.name_en,
                x=excluded.x,
                y=excluded.y,
                tags=excluded.tags,
                open_time=excluded.open_time,
                visit_minutes=excluded.visit_minutes,
                image_url=excluded.image_url,
                summary=excluded.summary,
                story=excluded.story
            """,
            {**poi, "tags": json.dumps(poi["tags"], ensure_ascii=False)},
        )
    return get_poi(poi["id"]) or poi


def list_edges() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM poi_edge").fetchall()
    return [dict(row) | {"recommended": bool(row["recommended"])} for row in rows]


def list_docs() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM knowledge_doc").fetchall()
    return [row_to_doc(row) for row in rows]


def get_session(session_id: str) -> dict:
    with connect() as conn:
        row = conn.execute("SELECT * FROM guide_session WHERE id = ?", (session_id,)).fetchone()
        if not row:
            conn.execute("INSERT INTO guide_session (id) VALUES (?)", (session_id,))
            return {"id": session_id, "language": None, "current_poi_id": None, "history": []}
    data = dict(row)
    data["history"] = json.loads(data["history"])
    return data


def update_session(session_id: str, language: str | None, current_poi_id: str | None, history: list[dict]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO guide_session (id, language, current_poi_id, history, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                language=excluded.language,
                current_poi_id=excluded.current_poi_id,
                history=excluded.history,
                updated_at=CURRENT_TIMESTAMP
            """,
            (session_id, language, current_poi_id, json.dumps(history, ensure_ascii=False)),
        )


def log_qa(session_id: str, message: str, answer: str, intent: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO qa_log (session_id, message, answer, intent) VALUES (?, ?, ?, ?)",
            (session_id, message, answer, intent),
        )
