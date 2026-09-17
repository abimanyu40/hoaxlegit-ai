import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "history.db"


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            message TEXT NOT NULL,
            verdict TEXT,
            sources TEXT,
            source_input TEXT DEFAULT 'text'
        )
    """)
    conn.commit()
    conn.close()


def save_check(message: str, verdict: str, sources: list, source_input: str = "text"):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO checks (timestamp, message, verdict, sources, source_input) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), message, verdict, json.dumps(sources), source_input)
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM checks ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def find_cached(message: str):
    """Cek apakah pesan yang sama persis pernah dicek sebelumnya."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM checks WHERE message = ? ORDER BY id DESC LIMIT 1", (message,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
