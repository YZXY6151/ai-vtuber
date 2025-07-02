import os
import sqlite3
from typing import List, Dict

DB_PATH = os.getenv("STM_DB_PATH", os.path.join(os.path.dirname(__file__), "../short_term_memory.db"))

def query_recent_memories(session_id: str, limit: int = 5, include_important: bool = True, exclude_empty: bool = True,include_expired: bool = False) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT content, created_at, important
        FROM short_term_memory
        WHERE session_id = ?
    """
    params = [session_id]

    if exclude_empty:
        query += " AND content IS NOT NULL AND TRIM(content) != ''"
    if not include_important:
        query += " AND important = 0"
    if not include_expired:
        query += " AND (expires_at IS NULL OR datetime(expires_at) > datetime('now'))"

    query += " ORDER BY datetime(created_at) DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    return [
        { "content": row[0], "created_at": row[1], "important": bool(row[2]) }
        for row in rows
    ]
