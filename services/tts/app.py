import os
import io
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gtts import gTTS
from fastapi.responses import StreamingResponse

app = FastAPI()

# 修改后的 CORS 配置：允许本地前端地址
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    lang: str = "zh-cn"       # 支持通过请求参数指定语种，默认简体中文
    slow: bool = False        # gTTS 的 slow 参数

async def synthesize_to_buffer(text: str, lang: str, slow: bool) -> io.BytesIO:
    """
    在线程池中异步调用 gTTS，将生成的音频写入 BytesIO 并返回。
    """
    loop = asyncio.get_event_loop()
    buf = io.BytesIO()
    def _generate():
        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf

    return await loop.run_in_executor(None, _generate)

@app.post("/api/tts/synthesize")
async def synthesize(req: TTSRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="文本不能为空")
    if len(text) > 500:
        text = text[:500]

    try:
        buf = await synthesize_to_buffer(text, req.lang, req.slow)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音合成失败：{e}")

    def iterfile():
        while True:
            chunk = buf.read(1024 * 8)
            if not chunk:
                break
            yield chunk

    return StreamingResponse(iterfile(), media_type="audio/mpeg")
