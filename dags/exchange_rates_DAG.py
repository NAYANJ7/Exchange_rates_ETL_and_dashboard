# dags/exchange_rates_DAG.py
"""
Robust 3-task DAG (fetch -> transform -> load).
This DAG tries to import user's etl package (common names).
If imports fail, it uses small fallback implementations so Airflow can run.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging, os, sys

# Make project root importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
ETL_PATH = os.path.join(PROJECT_ROOT, "etl")
if ETL_PATH not in sys.path:
    sys.path.insert(0, ETL_PATH)

# Try to import common user ETL modules; provide safe fallbacks if missing.
fetch_rates = None
transform_rates_to_df = None
try:
    # prefer common names used earlier
    from etl.fetch_data import fetch_rates as _f1
    fetch_rates = _f1
except Exception:
    try:
        from etl.fetch_data import fetch_rates as _f2
        fetch_rates = _f2
    except Exception:
        fetch_rates = None

try:
    from etl.transform import transform_rates_to_df as _t1
    transform_rates_to_df = _t1
except Exception:
    try:
        from etl.transform import transform_rates_to_df as _t2
        transform_rates_to_df = _t2
    except Exception:
        transform_rates_to_df = None

# loader import must exist (we provided loader.py). If import fails, that will raise at parse time.
from etl.loader import load_df_to_postgres, get_effective_db_url  # loader.py must provide these

# Fallback implementations (only used if user's etl.fetcher/transform missing)
if fetch_rates is None:
    import requests
    from datetime import datetime, timezone

    def fetch_rates():
        """Fallback fetch: calls exchangerate-api (same endpoint you provided)."""
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        j = resp.json()
        # convert to expected structure
        return {
            "base": j.get("base", "USD"),
            "rates": j.get("rates", {}),
            "fetched_at": datetime.now(timezone.utc),
            "source": url,
        }

if transform_rates_to_df is None:
    import pandas as pd

    def transform_rates_to_df(payload: dict) -> pd.DataFrame:
        """
        Fallback transform: turns payload['rates'] dict into DataFrame with columns:
        base_currency, target_currency, rate, fetched_at, source
        """
        rows = []
        base = payload.get("base", "USD")
        fetched_at = payload.get("fetched_at")
        source = payload.get("source")
        rates = payload.get("rates", {}) or {}
        for tgt, rate in rates.items():
            rows.append({
                "base_currency": base,
                "target_currency": tgt,
                "rate": rate,
                "fetched_at": fetched_at,
                "source": source,
            })
        df = pd.DataFrame(rows)
        return df

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="exchange_rates_pipeline_3task",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2025, 1, 1),
    schedule_interval="0 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["exchange", "rates"],
) as dag:

    def task_fetch(**context):
        logging.info("Starting fetch_rates()")
        payload = fetch_rates()
        # ensure fetched_at is a datetime object (fallback gives datetime)
        fetched = payload.get("fetched_at")
        # make XCom-safe: convert to ISO string
        payload_serializable = {
            "base": payload.get("base", "USD"),
            "rates": payload.get("rates", {}),
            "source": payload.get("source"),
            "fetched_at": fetched.isoformat() if hasattr(fetched, "isoformat") else str(fetched),
        }
        logging.info("Fetched %d rates", len(payload_serializable["rates"]))
        return payload_serializable

    def task_transform(**context):
        import pandas as pd
        from datetime import datetime

        ti = context["ti"]
        payload = ti.xcom_pull(task_ids="fetch_rates_task")
        if not payload:
            raise ValueError("No payload from fetch_rates_task")

        # convert fetched_at back to datetime for transform
        payload["fetched_at"] = datetime.fromisoformat(payload["fetched_at"])

        df = transform_rates_to_df(payload)
        # make XCom-safe: convert datetimes to string
        if "fetched_at" in df.columns:
            df["fetched_at"] = df["fetched_at"].astype(str)
        rows = df.to_dict(orient="records")
        logging.info("Transformed into %d rows", len(rows))
        return rows

    def task_load(**context):
        import pandas as pd
        ti = context["ti"]
        rows = ti.xcom_pull(task_ids="transform_rates_task")
        if not rows:
            logging.info("No rows to load; exiting.")
            return
        df = pd.DataFrame(rows)
        # convert fetched_at back to datetime with tz before writing
        if "fetched_at" in df.columns:
            df["fetched_at"] = pd.to_datetime(df["fetched_at"], utc=True, errors="coerce")
            df = df.dropna(subset=["fetched_at"])
        logging.info("Using DB URL: %s", get_effective_db_url() if callable(get_effective_db_url) else "unknown")
        load_df_to_postgres(df)
        logging.info("Loaded %d rows into Postgres", len(df))

    fetch = PythonOperator(task_id="fetch_rates_task", python_callable=task_fetch)
    transform = PythonOperator(task_id="transform_rates_task", python_callable=task_transform)
    load = PythonOperator(task_id="load_rates_task", python_callable=task_load)

    fetch >> transform >> load
