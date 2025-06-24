# services/nlp/app.py

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

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

# 请求模型
class ChatRequest(BaseModel):
    message: str
    persona: str = "gentle"

# Ollama 模型地址与模型名
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# 聊天接口
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
        return {
            "reply": data["message"]["content"]
        }
    except Exception as e:
        return {
            "reply": f"[错误] 无法连接到 Ollama 模型：{e}"
        }
