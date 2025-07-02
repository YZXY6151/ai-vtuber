# generate_response_test.py

from services.nlp.persona_manager import PersonaManager
from services.nlp.db.session_db import create_session

def test_generate_response():
    print("🧪 准备测试 AI 回复生成流程...")

    # 创建新的 session，绑定 gentle persona
    session_id = create_session(user_id="test-user", persona_id="gentle")
    
    print(f"📌 测试 session 创建完成: {session_id}（persona: gentle）")

    # 模拟用户输入
    user_input = "我今天有点烦躁，你能帮我放松一下心情吗？"

    # 实例化 PersonaManager 并生成回复（只触发一次 persona 加载）
    reply = PersonaManager(session_id).generate_response(session_id, user_input)

    # 打印结果
    print("\n🎯 用户输入:")
    print(user_input)
    print("\n🤖 AI 回复:")
    print(reply)

if __name__ == "__main__":
    test_generate_response()
