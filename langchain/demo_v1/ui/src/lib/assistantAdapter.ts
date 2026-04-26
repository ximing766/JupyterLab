import type { ChatModelAdapter, ThreadMessage } from "@assistant-ui/react";

type BackendChatResponse = {
  content: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://127.0.0.1:8000";

const buildText = (message: ThreadMessage): string => {
  return message.content
    .map((part) => (part.type === "text" ? part.text : ""))
    .join("")
    .trim();
};

const toBackendMessages = (messages: readonly ThreadMessage[]) => {
  return messages
    .filter((message) => message.role === "user" || message.role === "assistant")
    .map((message) => ({
      role: message.role,
      content: buildText(message),
    }));
};

export const localChatModelAdapter: ChatModelAdapter = {
  async *run({ messages, abortSignal }) {
    const response = await fetch(`${API_BASE_URL}/chat_stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        thread_id: "ui-local-thread",
        messages: toBackendMessages(messages),
      }),
      signal: abortSignal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Backend request failed: ${response.status} ${errorText}`);
    }

    if (!response.body) {
      throw new Error("No response body");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let content = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        content += decoder.decode(value, { stream: true });
        
        yield {
          content: [
            {
              type: "text",
              text: content,
            },
          ],
        };
      }
    } finally {
      reader.releaseLock();
    }
  },
};
