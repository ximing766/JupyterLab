import sys
from langchain_core.messages import AIMessageChunk

def stream_agent_responses(agent, query: str, thread_id: str = "default_thread"):
    """
    封装 Agent 的 Token 级流式输出逻辑。
    """
    print(f"USER: {query}\n")
    print("AGENT: ", end="", flush=True)
    
    # 使用 stream_mode="messages" 捕获每一个 Token
    for chunk, metadata in agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="messages"
    ):
        # 1. 处理工具调用状态
        if isinstance(chunk, AIMessageChunk) and chunk.tool_call_chunks:
            tool_names = [tc.get('name') for tc in chunk.tool_call_chunks if tc.get('name')]
            if tool_names:
                sys.stdout.write(f"\n[系统通知: 正在调用工具 {tool_names}...]\n")
                sys.stdout.flush()

        # 2. 处理文本 Token (打字机效果)
        elif isinstance(chunk, AIMessageChunk) and chunk.content:
            token = chunk.content
            sys.stdout.write(token)
            sys.stdout.flush()

    print("\n\n[End of Response]")
