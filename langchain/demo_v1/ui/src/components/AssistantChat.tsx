"use client";

import { useMemo } from "react";
import {
  AssistantRuntimeProvider,
  AuiProvider,
  useLocalRuntime,
  MessagePrimitive,
} from "@assistant-ui/react";
import { Thread, UserMessage } from "@assistant-ui/react-ui";
import { localChatModelAdapter } from "@/lib/assistantAdapter";
import { UserIcon } from "lucide-react";

const MyCustomUserMessage = () => {
  return (
    <UserMessage.Root>
      {/* 用户头像，对齐 Agent 头像位置 */}
      <div className="col-start-1 row-span-full mr-4 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white shrink-0 shadow-sm mt-1">
        <UserIcon size={16} />
      </div>
      
      <UserMessage.Attachments />
      <MessagePrimitive.If hasContent>
        <UserMessage.Content />
      </MessagePrimitive.If>
    </UserMessage.Root>
  );
};

export function AssistantChat() {
  const runtime = useLocalRuntime(useMemo(() => localChatModelAdapter, []));

  return (
    <AuiProvider>
      <AssistantRuntimeProvider runtime={runtime}>
        <div className="flex flex-col h-full w-full p-4 md:p-6 lg:p-8 z-10 relative">
          <div className="flex-1 w-full max-w-4xl mx-auto bg-white/80 dark:bg-black/60 backdrop-blur-xl shadow-2xl sm:rounded-3xl overflow-hidden border border-white/50 dark:border-neutral-800/50 ring-1 ring-black/5 dark:ring-white/10 flex flex-col">
            <Thread
              welcome={{
                message: "你好！我是基于 LangChain 和 Volcano 引擎构建的智能助手，请问有什么可以帮到您？",
              }}
              strings={{
                composer: {
                  input: {
                    placeholder: "输入您的问题...",
                  },
                },
              }}
              components={{
                UserMessage: MyCustomUserMessage,
              }}
            />
          </div>
        </div>
      </AssistantRuntimeProvider>
    </AuiProvider>
  );
}
