# utils/data_utils.py
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import requests
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------------------------------------
# ONE PLACE for the key – never exported directly
# ----------------------------------------------------------------------
_MASSIVE_API_KEY = os.getenv("MASSIVE_API_KEY")
if not _MASSIVE_API_KEY:
    raise ValueError("POLYGON_API_KEY not set in .env")

MASSIVE_BASE_URL = "https://api.massive.com"

# ----------------------------------------------------------------------
# Massive API wrapper (the ONLY public symbol from this module)
# ----------------------------------------------------------------------
def fetch_massive_data(endpoint: str, params: Optional[Dict[str, Any]] = None) -> dict:
    """GET wrapper for the Massive API."""
    url = f"{MASSIVE_BASE_URL}/{endpoint}"
    query: Dict[str, Any] = {"apiKey": _MASSIVE_API_KEY}
    if params:
        query.update(params)

    resp = requests.get(url, params=query, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ----------------------------------------------------------------------
# Helper to expose the key ONLY to the portfolio module (internal)
# ----------------------------------------------------------------------
def _get_api_key() -> str:
    """Return the stored API key – used only by portfolio.py."""
    return _MASSIVE_API_KEY


# ----------------------------------------------------------------------
# Simple in-memory Yahoo cache (TTL = 60 s)
# ----------------------------------------------------------------------
_yahoo_cache: dict[str, tuple[float, datetime]] = {}
YAHOO_TTL = timedelta(seconds=60)


def _cache_is_fresh(symbol: str) -> bool:
    price, ts = _yahoo_cache.get(symbol.upper(), (0.0, datetime.min))
    return datetime.utcnow() - ts < YAHOO_TTL


def get_cached_yahoo_price(symbol: str) -> Optional[float]:
    """Return a fresh Yahoo price or ``None``."""
    sym = symbol.upper()
    if _cache_is_fresh(sym):
        return _yahoo_cache[sym][0]

    # ---- Yahoo Finance via RapidAPI (free tier) --------------------
    url = "https://yh-finance.p.rapidapi.com/market/v2/get-quotes"
    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_YAHOO_KEY", ""),
        "x-rapidapi-host": "yh-finance.p.rapidapi.com",
    }
    params = {"symbols": sym, "region": "US"}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        price = float(data["quoteResponse"]["result"][0]["regularMarketPrice"])
        _yahoo_cache[sym] = (price, datetime.utcnow())
        return price
    except Exception as exc:
        logging.warning(f"[Yahoo] failed for {sym}: {exc}")
        return None