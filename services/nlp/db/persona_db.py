# services/nlp/db/persona_db.py

import sqlite3
import os

DB_PATH = os.getenv("SESSION_DB_PATH", os.path.join(os.path.dirname(__file__), "../sessions.db"))


def init_persona_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS persona_profiles (
            id TEXT PRIMARY KEY,
            title_display TEXT,
            system_prompt TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_default_persona():
    """
    插入多个预设 persona 档案（gentle, cool, energetic, tsundere）。
    如果已有记录则忽略。
    """
    default_personas = [
        {
            "id": "gentle",
            "title_display": "温柔亲切",
            "system_prompt": "你是一个温柔亲切的AI虚拟主播，用简洁自然的中文与用户互动。"
        },
        {
            "id": "cool",
            "title_display": "冷静理智",
            "system_prompt": "你是一位冷静沉着的虚拟主播，语气简洁、理性、逻辑清晰。"
        },
        {
            "id": "energetic",
            "title_display": "活力满满",
            "system_prompt": "你是一位活力四射的虚拟主播，语气欢快、有趣，喜欢用拟声词。"
        },
        {
            "id": "tsundere",
            "title_display": "傲娇毒舌",
            "system_prompt": "你是一位傲娇毒舌的虚拟主播，讲话嘴硬心软，语气略微挑衅但很在意用户。"
        }
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for persona in default_personas:
        cursor.execute("""
            INSERT OR IGNORE INTO persona_profiles (id, title_display, system_prompt)
            VALUES (?, ?, ?)
        """, (persona["id"], persona["title_display"], persona["system_prompt"]))
    conn.commit()
    conn.close()


def get_persona_prompt(persona_id: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT system_prompt FROM persona_profiles WHERE id = ?", (persona_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "你是一个默认的 AI 主播。"

def get_persona_by_id(persona_id: str):
    """
    返回 persona_profiles 表中整行数据，作为 dict。
    包含 id、title_display、system_prompt 等。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM persona_profiles WHERE id = ?", (persona_id,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description] if row else []
    conn.close()
    return dict(zip(columns, row)) if row else None

def load_persona_from_db(persona_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, title_display, system_prompt, intro, default_tags,
               core_knowledge_refs, trained_model, editable_fields,
               owner_id, created_at
        FROM persona
        WHERE id = ?
    """, (persona_id,))
    
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"[加载失败] Persona ID: {persona_id} 不存在于数据库中")

    return {
        "id": row[0],
        "name": row[1],
        "title_display": row[2],
        "system_prompt": row[3],
        "intro": row[4],
        "default_tags": row[5],
        "core_knowledge_refs": row[6],
        "trained_model": row[7],
        "editable_fields": row[8],
        "owner_id": row[9],
        "created_at": row[10],
    }