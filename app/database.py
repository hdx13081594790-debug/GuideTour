from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.seed_data import EDGES, KNOWLEDGE_DOCS, POIS

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.getenv("GUIDETOUR_SQLITE_PATH", DATA_DIR / "guidetour.db"))


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS poi (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                name_en TEXT NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                tags TEXT NOT NULL,
                open_time TEXT NOT NULL,
                visit_minutes INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                summary TEXT NOT NULL,
                story TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS poi_edge (
                from_poi_id TEXT NOT NULL,
                to_poi_id TEXT NOT NULL,
                distance_m INTEGER NOT NULL,
                walk_minutes INTEGER NOT NULL,
                recommended INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (from_poi_id, to_poi_id)
            );

            CREATE TABLE IF NOT EXISTS knowledge_doc (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                poi_id TEXT,
                language TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS guide_session (
                id TEXT PRIMARY KEY,
                language TEXT,
                current_poi_id TEXT,
                history TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS qa_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message TEXT NOT NULL,
                answer TEXT NOT NULL,
                intent TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        existing = conn.execute("SELECT COUNT(*) FROM poi").fetchone()[0]
        if existing == 0:
            seed(conn)


def seed(conn: sqlite3.Connection) -> None:
    for poi in POIS:
        conn.execute(
            """
            INSERT INTO poi VALUES (:id, :name, :name_en, :x, :y, :tags,
            :open_time, :visit_minutes, :image_url, :summary, :story)
            """,
            {**poi, "tags": json.dumps(poi["tags"], ensure_ascii=False)},
        )

    for from_id, to_id, distance_m, walk_minutes in EDGES:
        for a, b in [(from_id, to_id), (to_id, from_id)]:
            conn.execute(
                "INSERT INTO poi_edge VALUES (?, ?, ?, ?, 1)",
                (a, b, distance_m, walk_minutes),
            )

    for doc in KNOWLEDGE_DOCS:
        conn.execute(
            "INSERT INTO knowledge_doc VALUES (:id, :title, :poi_id, :language, :content, :tags)",
            {**doc, "tags": json.dumps(doc["tags"], ensure_ascii=False)},
        )
    for poi in POIS:
        conn.execute(
            "INSERT INTO knowledge_doc VALUES (?, ?, ?, ?, ?, ?)",
            (
                f"poi_{poi['id']}",
                f"{poi['name']}讲解",
                poi["id"],
                "zh",
                f"{poi['summary']}\n{poi['story']}",
                json.dumps(poi["tags"], ensure_ascii=False),
            ),
        )


def row_to_poi(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["tags"] = json.loads(item["tags"])
    return item


def row_to_doc(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["tags"] = json.loads(item["tags"])
    return item
