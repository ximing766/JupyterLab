# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Agent

```bash
# Interactive REPL
python main.py

# Single-shot query
python main.py "今天几号？"
```

## Architecture

This is a minimal **LangGraph agentic loop** backed by the ByteDance Ark API (DeepSeek-V3 model via OpenAI-compatible endpoint).

**Execution flow:**

```
User input → model_node → should_continue ──► END
                               │
                            "tools"
                               ↓
                           tool_node → (back to model_node)
```

**Module responsibilities:**

| File | Role |
|------|------|
| `config.py` | All constants: API key, model name, system prompt (Chinese) |
| `state.py` | `AgentState` TypedDict — single `messages` field with `add_messages` reducer |
| `tools.py` | Tool definitions; add new tools to `ALL_TOOLS` list and they're auto-registered |
| `nodes.py` | `model_node`, `tool_node` (prebuilt `ToolNode`), `should_continue` router |
| `graph.py` | Assembles the `StateGraph`, compiles with `InMemorySaver` checkpointer; exports module-level `graph` singleton |
| `main.py` | Entry point: streaming REPL or single-shot mode; each run gets a fresh UUID `thread_id` |

**Key design points:**
- The LLM is bound to tools at module load time in `nodes.py` (`_llm = _build_llm().bind_tools(ALL_TOOLS)`). Adding a tool requires only appending to `ALL_TOOLS` in `tools.py`.
- `InMemorySaver` provides in-process conversation history per `thread_id`. History is lost when the process exits.
- Streaming uses `stream_mode="messages"` and filters for `AIMessageChunk` to print tokens as they arrive.
- The system prompt (in `Config.SYSTEM_PROMPT`) instructs the model to call tools for real-time info and suppress `<think>` tags in output.

## Dependencies

No lockfile exists. Key packages: `langchain`, `langchain-openai`, `langgraph`, `langgraph-checkpoint`, `langgraph-prebuilt`.
