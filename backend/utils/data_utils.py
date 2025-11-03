import os
import requests
from dotenv import load_dotenv

load_dotenv()

MASSIVE_API_KEY = os.getenv("POLYGON_API_KEY")
MASSIVE_BASE_URL = "https://api.massive.com"

def fetch_massive_data(endpoint: str, params: dict = None):
    """Wrapper for Massive API requests"""
    if not MASSIVE_API_KEY:
        raise ValueError("MASSIVE_API_KEY not configured in .env")

    url = f"{MASSIVE_BASE_URL}/{endpoint}"
    query = {"apiKey": MASSIVE_API_KEY}
    if params:
        query.update(params)

    resp = requests.get(url, params=query, timeout=10)
    resp.raise_for_status()
    return resp.json()