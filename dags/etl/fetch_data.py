# etl/fetcher.py
import requests
from datetime import datetime, timezone

API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

def fetch_rates(timeout=15):
    """
    Fetch the latest exchange rates JSON from the API.
    Returns dict: { "base": str, "rates": dict, "fetched_at": datetime, "source": str }
    Raises requests.HTTPError on non-2xx responses.
    """
    resp = requests.get(API_URL, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    fetched_at = datetime.now(timezone.utc)
    return {
        "base": data.get("base", "USD"),
        "rates": data.get("rates", {}),
        "fetched_at": fetched_at,
        "source": API_URL,
    }
