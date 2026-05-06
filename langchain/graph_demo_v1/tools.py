import urllib.request
import http.client
from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_core.tools import tool


@tool
def get_current_datetime() -> str:
    """Get the current date and time (Beijing time)."""
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")


@tool
def fetch_text_from_url(url: str) -> str:
    """Fetch plain text content from a URL."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; langgraph-agent/1.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except http.client.IncompleteRead as e:
        raw = e.partial
    except urllib.error.URLError as e:
        return f"Fetch failed: {e}"

    if not raw:
        return "Fetch failed: No data received."
    return raw.decode("utf-8", errors="replace")


@tool
def calculate(expression: str) -> str:
    """Evaluate a safe arithmetic expression, e.g. '2 ** 10 + 3 * 4'."""
    print(f"tools calls calculate: {expression}")
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        return "Error: expression contains disallowed characters."
    try:
        result = eval(expression, {"__builtins__": {}})  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {e}"


# ── Registry ──────────────────────────────────────────────────────────────────
# Add new tools here; graph/nodes.py picks them up automatically.
ALL_TOOLS = [
    get_current_datetime,
    fetch_text_from_url,
    calculate,
]
