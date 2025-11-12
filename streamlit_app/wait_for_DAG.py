#!/usr/bin/env python3
"""
wait_for_dag.py
Waits until the Airflow metadata DB has at least one successful dag_run.
Reads EXCHANGE_DB_URL or AIRFLOW_DB_URL from env.
Exits 0 when found (or on timeout).
"""

import os
import time
import sys
import urllib.parse
import psycopg2

MAX_WAIT = int(os.getenv("MAX_WAIT", "60"))   # seconds
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", "8"))

# Prefer AIRFLOW_DB_URL then EXCHANGE_DB_URL
db_url = os.getenv("AIRFLOW_DB_URL") or os.getenv("EXCHANGE_DB_URL")
if not db_url:
    print("No AIRFLOW_DB_URL or EXCHANGE_DB_URL provided — skipping wait.")
    sys.exit(0)

# Parse the URL into connection params
def parse_pg(url):
    # support typical postgresql://user:pass@host:port/dbname
    p = urllib.parse.urlparse(url)
    user = p.username or ""
    password = p.password or ""
    host = p.hostname or "localhost"
    port = p.port or 5432
    dbname = p.path.lstrip("/") or ""
    return dict(user=user, password=password, host=host, port=port, dbname=dbname)

conn_info = parse_pg(db_url)
start = time.time()
print(f"Waiting up to {MAX_WAIT}s for a successful DAG run in {conn_info.get('host')}...")

while True:
    try:
        conn = psycopg2.connect(
            dbname=conn_info["dbname"],
            user=conn_info["user"],
            password=conn_info["password"],
            host=conn_info["host"],
            port=conn_info["port"],
            connect_timeout=5,
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM dag_run WHERE state='success';")
        rows = cur.fetchone()
        count = rows[0] if rows else 0
        cur.close()
        conn.close()
        if count and int(count) > 0:
            print(f"Found {count} successful DAG run(s). Proceeding.")
            sys.exit(0)
        else:
            elapsed = int(time.time() - start)
            if elapsed >= MAX_WAIT:
                print(f"Timeout reached ({MAX_WAIT}s). Proceeding anyway.")
                sys.exit(0)
            if elapsed % 30 == 0:
                print(f"Still waiting... {elapsed}s elapsed.")
    except Exception as e:
        # continue waiting; print every 30s
        elapsed = int(time.time() - start)
        if elapsed % 30 == 0:
            print(f"DB not ready or query failed ({e}). Still waiting... {elapsed}s elapsed.")
        if elapsed >= MAX_WAIT:
            print(f"Timeout reached ({MAX_WAIT}s). Proceeding anyway.")
            sys.exit(0)

    time.sleep(SLEEP_INTERVAL)
