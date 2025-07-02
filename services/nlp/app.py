from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from .persona_manager import PersonaManager
from .memory.short_term import query_recent_memories
from .utils.memory_logger import log_memory_event



# ───────────── persona 对应 prompt ─────────────
PERSONA_PROMPTS = {
    "gentle": "你是一个温柔亲切的AI虚拟主播，用简洁自然的中文与用户互动。",
    "tsundere": "你是一位傲娇毒舌的虚拟主播，讲话嘴硬心软，语气略微挑衅。",
    "energetic": "你是一位活力满满的虚拟主播，语气欢快、有趣，喜欢用拟声词。",
    "cool": "你是一位冷静沉着的主播，回答简洁逻辑清晰，话不多但很准确。",
}

# ───────────── 读取 prompt.txt（若存在） ─────────────
def load_prompt_file(path="prompt.txt"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"[警告] prompt.txt 不存在或读取失败，将使用 persona 设置：{e}")
        return None

custom_prompt = load_prompt_file()

# ───────────── FastAPI 设置 ─────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def build_full_prompt(session_id: str) -> str:
    manager = PersonaManager(session_id)
    persona = manager.persona or {}
    
    # 获取最近记忆（最多 5 条）
    memories = query_recent_memories(session_id=session_id, limit=5, include_important=True, exclude_empty=True)
    memory_summary = "\n".join([f"- {m['content']}" for m in memories]) if memories else "（无记忆）"

    # 构建完整系统 prompt
    template = manager.build_system_prompt()
    final_prompt = template.replace("{name}", persona.get("name", "AI")) \
                           .replace("{title_display}", persona.get("title_display", "虚拟主播")) \
                           .replace("{system_prompt}", persona.get("system_prompt", "")) \
                           .replace("{memory_summary}", memory_summary)

    log_memory_event("SYSTEM_PROMPT_BUILD", "构建系统 prompt 成功", session_id)
    return final_prompt


# 请求模型（原接口）
class ChatRequest(BaseModel):
    message: str
    persona: str = "gentle"

# Ollama 模型地址与模型名
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "yi:9b-chat")

# 聊天接口（原始）
@app.post("/api/nlp/chat")
async def chat_with_llama(req: ChatRequest):
    user_input = req.message.strip()
    persona = req.persona if req.persona in PERSONA_PROMPTS else "gentle"
    system_prompt = custom_prompt or PERSONA_PROMPTS[persona]

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

# ───────────── 新增：Session 模式的接口 ─────────────
from .persona_manager import PersonaManager  # 新增导入

class SessionChatRequest(BaseModel):
    session_id: str
    user_input: str

manager = PersonaManager()  # 初始化

@app.post("/api/nlp/chat_with_session")
def chat_with_session(req: SessionChatRequest):
    # try:
    #     reply = manager.generate_response(req.session_id, req.user_input)
    #     return { "reply": reply }
    # except Exception as e:
    #     return { "error": str(e) }
    system_prompt = build_full_prompt(req.session_id)

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.user_input}
        ],
        "stream": False
    }

    try:
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        return { "reply": data["message"]["content"] }
    except Exception as e:
        return { "error": f"[错误] 无法连接到模型：{e}" }

    

# ───────────── 初始化数据库 ─────────────
from .db.session_db import init_db
init_db()

# ───────────── 路由挂载 ─────────────
from .routes import session_routes
app.include_router(session_routes.router)