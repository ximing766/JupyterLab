from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent_core import create_literary_agent


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    thread_id: str = "ui-default-thread"


class ChatResponse(BaseModel):
    content: str


app = FastAPI(title="demo_v1 agent backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_agent = create_literary_agent()


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        return "".join(chunks).strip()
    return ""


def _extract_ai_text(invoke_result: Any) -> str:
    if not isinstance(invoke_result, dict):
        return ""

    messages = invoke_result.get("messages", [])
    if not isinstance(messages, list):
        return ""

    for message in reversed(messages):
        if getattr(message, "type", None) == "ai":
            return _extract_text(getattr(message, "content", ""))
        if isinstance(message, dict) and message.get("role") == "assistant":
            return _extract_text(message.get("content", ""))

    return ""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    invoke_input = {
        "messages": [
            {"role": message.role, "content": message.content}
            for message in payload.messages
        ]
    }
    result = _agent.invoke(
        invoke_input,
        config={"configurable": {"thread_id": payload.thread_id}},
    )
    content = _extract_ai_text(result)
    return ChatResponse(content=content)


@app.post("/chat_stream")
def chat_stream(payload: ChatRequest):
    invoke_input = {
        "messages": [
            {"role": message.role, "content": message.content}
            for message in payload.messages
        ]
    }

    def generate():
        from langchain_core.messages import AIMessageChunk
        for chunk, metadata in _agent.stream(
            invoke_input,
            config={"configurable": {"thread_id": payload.thread_id}},
            stream_mode="messages"
        ):
            # 1. 拦截工具调用，可以在前端展示
            if isinstance(chunk, AIMessageChunk) and chunk.tool_call_chunks:
                tool_names = [tc.get('name') for tc in chunk.tool_call_chunks if tc.get('name')]
                if tool_names:
                    yield f"\n> 🛠️ 系统通知: 正在调用工具 {', '.join(tool_names)}...\n\n"
            
            # 2. 拦截正常文本流
            elif isinstance(chunk, AIMessageChunk) and chunk.content:
                yield chunk.content

    return StreamingResponse(generate(), media_type="text/plain")
