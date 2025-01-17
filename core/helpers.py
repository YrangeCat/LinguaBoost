import json
import re
from core.errors import JSONParsingError

def remove_trailing_commas(json_string: str) -> str:
    """Removes trailing commas from a JSON string."""
    return re.sub(r',\s*([\]}])', r'\1', json_string)

def safe_json_loads(json_string: str, error_message: str = "Error decoding JSON") -> dict:
    """Safely loads a JSON string, raising a custom error on failure."""
    try:
        return json.loads(remove_trailing_commas(json_string))
    except json.JSONDecodeError as e:
        raise JSONParsingError(f"{error_message}: {e}")