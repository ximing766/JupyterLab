import os


class Config:
    """全局配置"""
    ARK_API_KEY: str = os.environ.get("ARK_API_KEY", "")
    BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    MODEL_NAME: str = "deepseek-v3-2-251201"
    TEMPERATURE: float = 0.5
    TIMEOUT: int = 300
    MAX_RETRIES: int = 3
    MAX_TOKENS: int = 25000

    SYSTEM_PROMPT: str = """你是一个知识渊博、表达能力强的助手。

## 能力与工具
- 需要实时信息时（日期、天气、网页内容）必须调用工具，严禁凭记忆回答。
- 只在必要时使用工具，避免冗余调用。

## 输出规范
- 直接输出最终回答，不要包含内部思考过程或 <think> 标签。
"""
