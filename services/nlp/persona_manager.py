# services/nlp/persona_manager.py

from typing import Optional, Dict
from services.nlp.db.session_db import get_session_by_id
from services.nlp.db.persona_db import get_persona_by_id
from services.nlp.utils.memory_logger import log_memory_event
from services.nlp.memory.short_term import query_recent_memories
from services.nlp.db.memory_db import store_short_term_memory
import requests
import os
from datetime import datetime
from services.nlp.db.persona_db import load_persona_from_db
from services.nlp.logs import log_persona_loaded



OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "yi:9b-chat")


class PersonaManager:
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.persona: Optional[Dict] = None
    
        if session_id:
            self.persona = self.get_persona_for_session(session_id)

    def get_persona_for_session(self, session_id: str) -> Optional[Dict]:
        session = get_session_by_id(session_id)
        if not session:
            log_memory_event("PERSONA_ERROR", f"未找到 session: {session_id}")
            return None
        persona_id = session.get("persona_id")
        if not persona_id:
            log_memory_event("PERSONA_ERROR", f"session 未绑定 persona: {session_id}")
            return None
        persona = get_persona_by_id(persona_id)
        if not persona:
            log_memory_event("PERSONA_ERROR", f"未找到 persona: {persona_id}")
            return None
        log_memory_event("LOAD_PERSONA", f"成功加载 persona: {persona.get('name', persona_id)}", session_id)
        log_memory_event("PERSONA_INFO", f"标题: {persona.get('title_display')} | Prompt: {persona.get('system_prompt')}", session_id)
        
        return persona
    
    def get_persona(self):
        if self._persona and self._persona_loaded_once:
            return self._persona

        # 从 session 表获取 persona_id
        session_data = get_session_by_id(self.session_id)
        if not session_data:
            raise ValueError(f"[PersonaManager] 无法找到 session: {self.session_id}")
        
        persona_id = session_data["persona_id"]

        # 从 persona 表加载 persona 详情
        self._persona = load_persona_from_db(persona_id)
        self._persona_loaded_once = True

        log_persona_loaded(self.session_id, self._persona)
        return self._persona


    def build_system_prompt(self, persona: Optional[Dict] = None) -> str:
        """
        构造最终 system prompt：支持从 prompt.txt 中加载模板，
        并插入 persona 信息、记忆、当前时间等。
        """
        source = persona if persona else self.persona
        if not source:
            return "你是一个AI助手，请用自然、友好的语气与用户交流。"

        # 读取模板
        prompt_path = os.getenv("PROMPT_TEMPLATE_PATH", "prompt.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                template = f.read()
        except Exception:
            template = "{system_prompt}\n\n记忆内容：\n{memory}"

        # 查询短期记忆
        memory_snippets = []
        if self.session_id:
            memories = query_recent_memories(self.session_id, limit=10)
            for m in memories:
                memory_snippets.append(f"- {m['content']}")
        memory_text = "\n".join(memory_snippets)

        # 构造替换变量
        variables = {
            "persona_title": source.get("title_display", ""),
            "system_prompt": source.get("system_prompt", ""),
            "memory": memory_text,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 执行替换
        for key, val in variables.items():
            template = template.replace("{" + key + "}", val)

        return template

    def generate_response(self, session_id: str, user_input: str) -> str:
        self.session_id = session_id
        self.persona = self.get_persona_for_session(session_id)
        if not self.persona:
            return "⚠️ 无法加载人格设定"

        # 查询短期记忆（最近 5 条）
        recent_list = query_recent_memories(session_id, limit=5)
        recent_text = "\n".join([f"- {m['content']}" for m in recent_list])

        # 构建系统 prompt
        system_prompt = self.build_system_prompt(self.persona)

        # 构造请求体
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "stream": False
        }

        # 请求模型
        try:
            response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            reply = data["message"]["content"]

            # 自动保存对话（写入短期记忆）
            store_short_term_memory(session_id, user_input)
            store_short_term_memory(session_id, reply)
            log_memory_event("AUTO_WRITE_MEMORY", f"保存用户输入 + AI 回复，重要: True", session_id)

            return reply
        except Exception as e:
            return f"[错误] 无法连接到 Ollama 模型：{e}"
