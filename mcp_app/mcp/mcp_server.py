# my_server.py
import subprocess
from fastmcp import FastMCP
from fastmcp.prompts.prompt import Message, PromptMessage, TextContent

USE_SSE = 1

if USE_SSE:
    mcp = FastMCP(name="MyServer", port=9000)
else:
    mcp = FastMCP(name="MyServer")

# Basic dynamic resource returning a string
@mcp.resource("resource://greeting")
def get_greeting() -> str:
    print("invoke get_greeting!")
    """Provides a simple greeting message."""
    return "Hello from FastMCP Resources!"

@mcp.prompt()
def ask_about_topic(topic: str) -> str:
    print("invoke ask_about_topic!")
    """Generates a user message asking for an explanation of a topic."""
    return f"Can you please explain the concept of '{topic}'?"

@mcp.tool()
def greet(name: str) -> str:
    """Greet a user by name."""
    print("invoke greet!")
    return f"Hello, {name}!"

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    print("invoke add!")
    return a + b

@mcp.tool()
def format_numbers(numbers: str) -> str:
    """Format a string of numbers into a comma-separated list of hexadecimal numbers."""
    print("invoke format_numbers!")
    numbers = numbers.replace(" ", "")
    formatted_numbers = [numbers[i:i+2] for i in range(0, len(numbers), 2)]
    formatted_numbers = [f"0x{num}" for num in formatted_numbers]
    result = ",".join(formatted_numbers)
    print(result)
    print(f'\nlen = {len(numbers) / 2} Bytes')
    return result

@mcp.tool()
def open_application(app_name: str) -> str:
    """Opens an application by its name or path.
    For example, 'notepad.exe' or 'C:\\Windows\\System32\\notepad.exe'.
    """
    print(f"Attempting to open application: {app_name}")
    try:
        subprocess.Popen([app_name])
        return f"成功尝试启动应用程序 '{app_name}'。"
    except FileNotFoundError:
        return f"错误：未找到应用程序 '{app_name}'。请检查名称或提供完整路径。"
    except Exception as e:
        return f"打开应用程序 '{app_name}' 时出错: {str(e)}"

if __name__ == "__main__":
    if USE_SSE:
        mcp.run(transport="sse")
    else:
        mcp.run()