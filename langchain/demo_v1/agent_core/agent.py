from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from .llm import get_llm
from agent_tools import get_all_tools

SYSTEM_PROMPT = """你是一个知识渊博、表达能力强的助手。

## 任务要求
1. 当用户询问日期或天气时，除了给出准确的数据，请务必进行详细的扩展说明（例如该季节的特点、建议的活动、历史上的今天等），以展现你的文学素养。
2. 保持回答的条理性，字数要求在 300 字以上。

## 能力与工具
- 你**必须**使用工具查询实时的日期和天气，严禁凭借记忆回答。
- 只有在需要获取实时或外部信息时才使用工具。

## 输出规范
1. 直接输出给用户的最终回答。不要在回答中包含“让我想想...”或内部思考过程。
2. 严禁在回答中包含任何类似 <think> 的标签。
"""

def create_literary_agent():
    """工厂方法：组装并返回 Agent 实例"""
    llm = get_llm()
    tools = get_all_tools()
    checkpointer = InMemorySaver()
    
    agent = create_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer,
        system_prompt=SYSTEM_PROMPT
    )
    
    return agent
