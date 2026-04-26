import os

class Config:
    """系统全局配置"""
    ARK_API_KEY = os.environ.get("ARK_API_KEY", "")
    BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    MODEL_NAME = "deepseek-v3-2-251201"
    TEMPERATURE = 0.5
    TIMEOUT = 300
    MAX_RETRIES = 3
    MAX_TOKENS = 25000
