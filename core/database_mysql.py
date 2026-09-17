import json
from datetime import datetime

import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "hoaxapp",
    "password": "password_lo",  # ganti sesuai yang dibuat pas CREATE USER
    "database": "hoax_checker",
}


def _get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            message TEXT NOT NULL,
            verdict TEXT,
            sources TEXT,
            source_input VARCHAR(20) DEFAULT 'text'
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()


def save_check(message: str, verdict: str, sources: list, source_input: str = "text"):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO checks (timestamp, message, verdict, sources, source_input) VALUES (%s, %s, %s, %s, %s)",
        (datetime.now(), message, verdict, json.dumps(sources), source_input)
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_history(limit: int = 20):
    conn = _get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM checks ORDER BY id DESC LIMIT %s", (limit,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def find_cached(message: str):
    conn = _get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM checks WHERE message = %s ORDER BY id DESC LIMIT 1", (message,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row
