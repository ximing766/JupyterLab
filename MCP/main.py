from fastmcp import FastMCP

mcp = FastMCP(name = "MyMCPTools",
                instructions = "Include all my hosted MCP tools here.",
            )

mcp.run(transport="sse",host="127.0.0.1",port=9001)   


