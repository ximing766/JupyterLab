from datetime import datetime
from langchain_core.tools import tool

@tool
def get_current_date() -> str:
    """获取当前的日期。"""
    return datetime.now().strftime("%Y-%m-%d")

@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}的天气是：晴朗，气温 25°C。"
