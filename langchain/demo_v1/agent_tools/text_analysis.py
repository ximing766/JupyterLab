import json
from langchain_core.tools import tool

@tool
def analyze_text_substrings(text: str, substring: str) -> str:
    """
    Analyzes a given text to find the total number of lines containing a specific substring, 
    and the 1-based line number of its first occurrence.
    
    Args:
        text: The complete text content to analyze.
        substring: The string to search for in each line (case-sensitive).
        
    Returns:
        A JSON string containing 'total_lines_with_substring' and 'first_occurrence_line'.
    """
    lines = text.split('\n')
    count = 0
    first_line = None
    
    for i, line in enumerate(lines):
        if substring in line:
            count += 1
            if first_line is None:
                first_line = i + 1
                
    result = {
        "total_lines_with_substring": count,
        "first_occurrence_line": first_line
    }
    return json.dumps(result)
