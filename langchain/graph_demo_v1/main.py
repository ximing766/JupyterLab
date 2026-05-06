"""
LangGraph Agent — entry point

Usage:
    python main.py                    # interactive REPL
    python main.py "今天几号？"        # single-shot query
"""
import sys
import uuid
from langchain_core.messages import HumanMessage, AIMessageChunk

from graph import graph


def run_streaming(user_input: str, thread_id: str) -> None:
    """Stream the agent response token-by-token to stdout."""
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=user_input)]}

    print("\nAssistant: ", end="", flush=True)
    for chunk, _ in graph.stream(inputs, config=config, stream_mode="messages"):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            print(chunk.content, end="", flush=True)
    print()  # newline after stream ends


def repl(thread_id: str) -> None:
    """Simple interactive loop."""
    print("LangGraph Agent  (输入 'exit' 或 Ctrl-C 退出)\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Bye!")
            break
        run_streaming(user_input, thread_id)


if __name__ == "__main__":
    session_id = str(uuid.uuid4())

    if len(sys.argv) > 1:
        # Single-shot mode: python main.py "your question"
        query = " ".join(sys.argv[1:])
        print(f"You: {query}")
        run_streaming(query, session_id)
    else:
        repl(session_id)
