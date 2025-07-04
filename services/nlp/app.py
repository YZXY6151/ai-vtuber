from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from datetime import datetime, timezone

from .persona_manager import PersonaManager
from .memory.short_term import query_recent_memories
from .utils.memory_logger import log_memory_event

# ───────────── FastAPI 设置 ─────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────── 请求模型（非 session 模式） ─────────────
class ChatRequest(BaseModel):
    message: str
    persona: str = "gentle"  # 保留字段但不使用

# ───────────── 请求模型（session 模式） ─────────────
class SessionChatRequest(BaseModel):
    session_id: str
    user_input: str

# ───────────── 模型配置 ─────────────
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "yi:9b-chat")

# ───────────── 简化版接口（不带 session）─────────────
@app.post("/api/nlp/chat")
async def chat_with_llama(req: ChatRequest):
    user_input = req.message.strip()
    system_prompt = "你是一个AI助手，请自然、友好地与用户互动。"

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "stream": False
    }

    try:
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        return { "reply": data["message"]["content"] }
    except Exception as e:
        return { "reply": f"[错误] 无法连接到 Ollama 模型：{e}" }

# ───────────── 带 Session 模式的正式接口 ─────────────
@app.post("/api/nlp/chat_with_session")
def chat_with_session(req: SessionChatRequest):
    try:
        session_id = req.session_id
        user_input = req.user_input.strip()

        # 限制注入最近 5 条短期记忆
        recent_memories = query_recent_memories(session_id=session_id, limit=10, with_ids=True)


        manager = PersonaManager(session_id)
        reply, meta = manager.generate_response(
            session_id=session_id,
            user_input=user_input,
            memory_list=recent_memories  # 明确传入限定后的记忆
        )

        return { "reply": reply, "meta": meta }

    except Exception as e:
        return {
            "reply": f"[错误] 无法生成回复：{e}",
            "meta": {
                "persona": "unknown",
                "used_memory": False,
                "injection_memory_ids": [],
                "memory_summary": "（无记忆）",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

# ───────────── 初始化数据库 ─────────────
from .db.session_db import init_db
init_db()

# ───────────── 路由挂载 ─────────────
from .routes import session_routes
app.include_router(session_routes.router)
