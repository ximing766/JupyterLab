import urllib.request
import http.client
from langchain_core.tools import tool

@tool
def fetch_text_from_url(url: str) -> str:
    """Fetch the document from a URL.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; quickstart-research/1.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except http.client.IncompleteRead as e:
        raw = e.partial
    except urllib.error.URLError as e:
        return f"Fetch failed: {e}"
    
    if not raw:
        return "Fetch failed: No data received."
        
    text = raw.decode("utf-8", errors="replace")
    return text
