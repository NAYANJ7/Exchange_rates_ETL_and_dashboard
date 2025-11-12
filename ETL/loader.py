# etl/loader.py
"""
Robust loader for Airflow ETL: writes exchange rate DataFrame into Postgres
and ensures connection works inside Docker.
"""

import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import urlparse, urlunparse

logging.basicConfig(level=logging.INFO)

def normalize_db_url(db_url: str) -> str:
    """
    If running inside a container, convert localhost:5433 to exchange-postgres:5432.
    """
    if not db_url:
        return db_url
    try:
        parsed = urlparse(db_url)
        host = parsed.hostname
        port = parsed.port
        if host in ("localhost", "127.0.0.1") and port in (5433, 5432):
            auth = ""
            if parsed.username:
                auth = parsed.username
                if parsed.password:
                    auth += ":" + parsed.password
                auth += "@"
            new_netloc = f"{auth}exchange-postgres:5432"
            new_parsed = parsed._replace(netloc=new_netloc)
            new_url = urlunparse(new_parsed)
            logging.info("Normalized DB URL from %s -> %s", db_url, new_url)
            return new_url
    except Exception as e:
        logging.warning("Could not normalize DB URL (%s): %s", db_url, e)
    return db_url

# Default and fallback DB URLs
DEFAULT_DB_URL_ENV = os.getenv("EXCHANGE_DB_URL", "")
FALLBACK_DB_URL = "postgresql://exchanger:exchanger@exchange-postgres:5432/exchange_db"

def get_effective_db_url():
    """
    Returns the final connection URL for the DAG to use.
    Prioritizes env var, otherwise uses fallback service-based connection.
    """
    if DEFAULT_DB_URL_ENV:
        return normalize_db_url(DEFAULT_DB_URL_ENV)
    return FALLBACK_DB_URL

def get_engine(db_url: str = None):
    db = db_url or get_effective_db_url()
    logging.info("Using DB URL for SQLAlchemy: %s", db)
    return create_engine(db, echo=False, pool_pre_ping=True)

def ensure_table(engine):
    """
    Creates exchange_rates table and indexes if not exist.
    """
    create_sql = '''
    CREATE TABLE IF NOT EXISTS exchange_rates (
        id SERIAL PRIMARY KEY,
        base_currency VARCHAR(10) NOT NULL,
        target_currency VARCHAR(10) NOT NULL,
        rate NUMERIC(18,8) NOT NULL,
        fetched_at TIMESTAMPTZ NOT NULL,
        source VARCHAR(255)
    );
    CREATE INDEX IF NOT EXISTS idx_exchange_rates_fetched_at ON exchange_rates(fetched_at);
    CREATE INDEX IF NOT EXISTS idx_exchange_rates_target ON exchange_rates(target_currency);
    '''
    with engine.begin() as conn:
        conn.execute(text(create_sql))

def load_df_to_postgres(df: pd.DataFrame, table_name: str = "exchange_rates", db_url: str = None):
    """
    Loads a pandas DataFrame into Postgres using SQLAlchemy.
    """
    if df is None or df.empty:
        logging.info("load_df_to_postgres: nothing to load.")
        return

    df = df.copy()
    expected = ["base_currency", "target_currency", "rate", "fetched_at", "source"]
    df = df[[c for c in expected if c in df.columns]]

    if "fetched_at" in df.columns:
        df["fetched_at"] = pd.to_datetime(df["fetched_at"], utc=True, errors="coerce")
    if "rate" in df.columns:
        df["rate"] = pd.to_numeric(df["rate"], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["target_currency", "rate", "fetched_at"])
    after = len(df)
    if after < before:
        logging.warning("Dropped %d invalid rows", before - after)

    if df.empty:
        logging.info("After cleaning, no rows to insert.")
        return

    engine = get_engine(db_url)
    try:
        ensure_table(engine)
        df.to_sql(table_name, con=engine, if_exists="append", index=False, method="multi", chunksize=500)
        logging.info("Inserted %d rows into %s", len(df), table_name)
    except SQLAlchemyError as e:
        logging.exception("Database error while inserting into %s: %s", table_name, e)
        raise
    finally:
        try:
            engine.dispose()
        except Exception:
            pass
