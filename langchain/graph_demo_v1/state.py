from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Graph state.

    messages: full conversation history; add_messages merges lists instead of
              overwriting, so parallel branches don't clobber each other.
    """
    messages: Annotated[list[AnyMessage], add_messages]
