import json
import os

def load_config(file_path="config.json"):
    """Load configuration from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

def format_response(success=True, message="", data=None):
    """Format API responses consistently."""
    return {"success": success, "message": message, "data": data or {}}
    