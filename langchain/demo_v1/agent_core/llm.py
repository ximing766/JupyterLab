from langchain_openai import ChatOpenAI
from .config import Config

def get_llm() -> ChatOpenAI:
    """初始化并返回 LLM 模型实例"""
    return ChatOpenAI(
        api_key=Config.ARK_API_KEY,
        base_url=Config.BASE_URL,
        model=Config.MODEL_NAME,
        temperature=Config.TEMPERATURE,
        timeout=Config.TIMEOUT,
        max_retries=Config.MAX_RETRIES,
        max_tokens=Config.MAX_TOKENS,
        streaming=True
    )
