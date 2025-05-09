import asyncio
from fastmcp import Client

print("Client Running")

# client = Client("http://localhost:9000/sse")
client = Client("mcp_server.py")
print(client.transport)



async def call_tool(name: str):
    async with client:
        
        tools = await client.list_tools()
        print(f"tools = {tools}\n")

        resources = await client.list_resources()
        print(f"resources = {resources}\n")

        prompts = await client.list_prompts()
        print(f"prompts = {prompts}\n")

        print(f"Client connected: {client.is_connected()}")
        result = await client.call_tool("greet", {"name": name})
        print(f"Available tools: {result[0].text}")
    
    print(f"Client connected: {client.is_connected()}")   # Connection is closed here 

asyncio.run(call_tool("Ford"))

