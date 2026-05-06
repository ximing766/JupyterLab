from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from state import AgentState
from nodes import model_node, tool_node, should_continue


def build_graph(checkpointer=None):
    """Assemble and compile the agent graph.

    Args:
        checkpointer: optional LangGraph checkpointer for persistence.
                      Defaults to InMemorySaver (in-process memory).

    Returns:
        Compiled LangGraph runnable.
    """
    # ── Step 6: Build ─────────────────────────────────────────────────────────
    builder = StateGraph(AgentState)

    builder.add_node("model", model_node)
    builder.add_node("tools", tool_node)

    builder.set_entry_point("model")

    builder.add_conditional_edges(
        "model",
        should_continue,
        {"tools": "tools", "end": END},
    )
    # After tools run, always go back to the model
    builder.add_edge("tools", "model")

    if checkpointer is None:
        checkpointer = InMemorySaver()

    return builder.compile(checkpointer=checkpointer)


# Module-level singleton — import this for quick use
graph = build_graph()
