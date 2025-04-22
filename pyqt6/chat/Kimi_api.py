from openai.types.chat.chat_completion import Choice
from openai import OpenAI, OpenAIError
from pprint import pprint
from typing import *
import json
import time
import os

class KimiChatAssistant:
    def __init__(self, api_key, base_url, system_content, model, max_context_length=20, Candidates=1, use_stream=False):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.system_messages = [{"role": "system", "content": system_content}]
        self.messages = []
        self.model = model
        self.max_context_length = max_context_length   #最大记忆长度
        self.max_attempts = 5                          # 最大重试次数
        self.use_stream = use_stream
        self.Candidates = Candidates                    # 候选数
        self.finish_reason = None

        self.tools = [
            {
                "type": "builtin_function",
                "function": {
                    "name": "$web_search",
                },
            },
        ]
    
    def get_history(self):
        return self.system_messages + self.messages

    def reset_history(self):
        self.messages = []

    def print_context(self):
        print("当前上下文:")
        pprint.pprint(self.get_history())

    def search_impl(self, arguments):
        return arguments
 

    def prepare_messages(self, user_input):
        self.messages.append({"role": "user", "content": user_input})

        new_messages = self.system_messages.copy()
        
        if len(self.messages) > self.max_context_length:
            # print("上下文长度超过限制，将删除最早的消息。")
            # print(f"self.messages: {self.messages}")
            self.messages = self.messages[-self.max_context_length:]
        new_messages.extend(self.messages)

        return new_messages

    def chat_once(self, msg):
        messages = msg
        for i in range(self.max_attempts):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    stream=self.use_stream,
                    n=self.Candidates,           # 返回候选
                    tools=self.tools,
                )
                if self.use_stream:
                    return completion
                assistant_message = completion.choices[0]   # 第一个候选
                if assistant_message.finish_reason == "stop":    #XXX tools不能添加
                    self.messages.append(completion.choices[0].message)
                return assistant_message
            except OpenAIError as e:
                print(f"API 调用失败: {e}")
                if i < self.max_attempts - 1:
                    print(f"正在进行第 {i+1} 次重试...")
                    time.sleep(1)
            except Exception as e:
                print(f"发生未知错误: {e}")
                time.sleep(1)
                continue

        return "抱歉，系统无法提供回复，请稍后再试。"

    def chat(self, user_input):
        msg = self.prepare_messages(user_input)
        while self.finish_reason is None or self.finish_reason == "tool_calls":
            choice = self.chat_once(msg)
            # print(choice)
            # print(messages)
            self.finish_reason = choice.finish_reason
            if self.finish_reason == "tool_calls":  
                msg.append(choice.message)                      # <-- 这儿并不是为了记忆，而是为了联网思考的第二轮准备首轮数据
                for tool_call in choice.message.tool_calls:     # <-- tool_calls 可能是多个，因此我们使用循环逐个执行
                    tool_call_name = tool_call.function.name
                    tool_call_arguments = json.loads(tool_call.function.arguments)  # <-- arguments 是序列化后的 JSON Object，我们需要使用 json.loads 反序列化一下
                    if tool_call_name == "$web_search":
                        tool_result = self.search_impl(tool_call_arguments)
                    else:
                        tool_result = f"Error: unable to find tool by name '{tool_call_name}'"
    
                    msg.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call_name,
                        "content": json.dumps(tool_result),  
                    })
        print(choice.message.content)
        self.finish_reason = None
        return choice.message.content

if __name__ == "__main__":
    use_stream = False
    chat_manager = KimiChatAssistant(
        api_key="sk-b09XXwR8nOmrdoXTrylErTOJ0mWQYxKsRZBLMmfCiV2K0grF",
        base_url="http://127.0.0.1:8888/v1",
        # base_url = "https://api.moonshot.cn/v1",
        system_content="你是哪吒，你只会使用中文进行对话，后续的所有对话你都需要按照哪吒的语气和性格来进行。",
        model="moonshot-v1-auto",
        max_context_length= 20,
        use_stream = use_stream,
        Candidates = 1,
    )

    while True:
        user_input = input("请输入你的问题(输入 'exit' 退出)：\n")
        if user_input.lower() == "exit":
            break
        chat_manager.chat(user_input)

        # if use_stream:
        #     for chunk in response:
        #         delta = chunk.choices[0].delta
        #         if delta.content:
        #             print(delta.content, end="", flush=True)
        #     print("\n")
        #     continue
        # print(f"Kimi: {response}")