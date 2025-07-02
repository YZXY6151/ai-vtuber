# init_db.py

import sqlite3
import os

# 确保 database 目录存在
os.makedirs("database", exist_ok=True)

db_path = "database/main.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 创建 persona_profiles 表
cursor.execute("""
CREATE TABLE IF NOT EXISTS persona_profiles (
    id TEXT PRIMARY KEY,
    title_display TEXT,
    system_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 创建 sessions 表
cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    persona_id TEXT,
    titlename TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 插入 persona 设定
persona_data = [
    ("gentle", "温柔", "你是一个温柔亲切的AI虚拟主播，用简洁自然的中文与用户互动。"),
    ("tsundere", "傲娇", "你是一位傲娇毒舌的虚拟主播，讲话嘴硬心软，语气略微挑衅。"),
    ("energetic", "活泼", "你是一位活力满满的虚拟主播，语气欢快、有趣，喜欢用拟声词。"),
    ("cool", "冷静", "你是一位冷静沉着的主播，回答简洁逻辑清晰，话不多但很准确。")
]

cursor.executemany("""
INSERT OR REPLACE INTO persona_profiles (id, title_display, system_prompt)
VALUES (?, ?, ?)
""", persona_data)

# 插入测试 session
cursor.execute("""
INSERT OR REPLACE INTO sessions (id, user_id, persona_id, titlename)
VALUES (?, ?, ?, ?)
""", ("abc123", "user001", "gentle", "测试会话"))

conn.commit()
conn.close()

print("✅ 数据库初始化完成：database/main.db")
