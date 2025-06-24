# services/nlp/app.py

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

# ───────────── 读取 prompt.txt ─────────────
def load_system_prompt(file_path="prompt.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"[警告] 无法读取 prompt.txt：{e}")
        return "你是一个中文AI助手。"

SYSTEM_PROMPT = load_system_prompt()
OLLAMA_URL    = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "llama3")

# ───────────── FastAPI 应用 ─────────────
app = FastAPI()

# 允许跨域请求
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

# 聊天接口
@app.post("/api/nlp/chat")
async def chat_with_llama(req: ChatRequest):
    user_input = req.message.strip()

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
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
