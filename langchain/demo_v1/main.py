from agent_core import create_literary_agent, stream_agent_responses

def main():
    # 1. 初始化 Agent
    agent = create_literary_agent()

    # 2. 交互查询
    query = "请帮我查一下今天是几号？另外我想知道北京今天的天气怎么样？请详细地告诉我。"

    # 3. 使用封装的流式输出函数
    stream_agent_responses(
        agent=agent, 
        query=query, 
        thread_id="streaming-demo-thread"
    )

if __name__ == "__main__":
    main()
