from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from config import Config
from state import AgentState
from tools import ALL_TOOLS


# ── Step 1: Model ─────────────────────────────────────────────────────────────
def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=Config.ARK_API_KEY,
        base_url=Config.BASE_URL,
        model=Config.MODEL_NAME,
        temperature=Config.TEMPERATURE,
        timeout=Config.TIMEOUT,
        max_retries=Config.MAX_RETRIES,
        max_tokens=Config.MAX_TOKENS,
        streaming=True,
    )


_llm = _build_llm().bind_tools(ALL_TOOLS)


# ── Step 3: Model node ────────────────────────────────────────────────────────
def model_node(state: AgentState) -> AgentState:
    """Call the LLM with the current message history."""
    messages = [SystemMessage(content=Config.SYSTEM_PROMPT)] + state["messages"]
    response = _llm.invoke(messages)
    return {"messages": [response]}


# ── Step 4: Tool node ─────────────────────────────────────────────────────────
# ToolNode automatically dispatches tool_calls from the last AI message.
tool_node = ToolNode(ALL_TOOLS)


# ── Step 5: End logic (routing) ───────────────────────────────────────────────
def should_continue(state: AgentState) -> str:
    """Return 'tools' if the model requested tool calls, else 'end'."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "end"
