# services/nlp/app.py  (Windows / CPU 版本)

import os, asyncio, logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ─────────── CORS ────────────
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS", "*") != "*" else ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])

# ─────────── 配置 ────────────
MODEL_NAME    = os.getenv("TRANSFORMER_MODEL", "Qwen/Qwen1.5-1.8B-Chat")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "你是一位友好的中文虚拟主播，用简短自然的中文回答用户。")
GEN_TEMP      = float(os.getenv("GEN_TEMP", 0.7))
TOP_P         = float(os.getenv("TOP_P", 0.9))

logger.info(f"Loading model on CPU: {MODEL_NAME}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model     = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True,
    torch_dtype="auto",   # 自动 fp16 / fp32
    low_cpu_mem_usage=True
)
logger.info("Model loaded.")

# ─────────── 数据模型 ────────────
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# ─────────── 路由 ────────────
@app.post("/api/nlp/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    user_msg = req.message.strip()[:500]
    if not user_msg:
        raise HTTPException(status_code=400, detail="输入不能为空")

    prompt = f"{SYSTEM_PROMPT}\n用户：{user_msg}\n主播："
    inputs = tokenizer(prompt, return_tensors="pt")  # CPU tensor

    try:
        outputs = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate(
                **inputs,
                max_new_tokens=80,
                temperature=GEN_TEMP,
                top_p=TOP_P,
                repetition_penalty=1.2,
                pad_token_id=tokenizer.eos_token_id
            )
        )

        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
        reply = decoded.split("主播：", 1)[-1].strip() or "好的～"
        return ChatResponse(reply=reply)

    except Exception as e:
        logger.exception("推理失败")
        raise HTTPException(status_code=500, detail="对话生成失败，请稍后重试")
