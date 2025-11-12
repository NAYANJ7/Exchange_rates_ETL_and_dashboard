# etl/transform_pandas.py
import pandas as pd

def transform_rates_to_df(fetch_payload):
    """
    Convert the fetcher payload to a pandas DataFrame ready for database insert.
    Columns: base_currency, target_currency, rate, fetched_at, source
    """
    base = fetch_payload["base"]
    fetched_at = fetch_payload["fetched_at"]
    source = fetch_payload.get("source")
    rates = fetch_payload.get("rates") or {}

    rows = []
    for currency, rate in rates.items():
        rows.append({
            "base_currency": base,
            "target_currency": currency,
            "rate": float(rate),
            "fetched_at": fetched_at,
            "source": source
        })

    df = pd.DataFrame(rows, columns=["base_currency", "target_currency", "rate", "fetched_at", "source"])
    return df
