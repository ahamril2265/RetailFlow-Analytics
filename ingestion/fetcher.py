"""
fetcher.py — Phase 1: Data Ingestion Layer
==========================================
Responsibilities:
  - Connect to FakeStore API endpoints
  - Retry with exponential backoff on failure
  - Save raw JSON to timestamped landing zone
  - Log every run with record counts and duration

Industry pattern: "Extract" step of ELT.
Raw data is NEVER modified here — store first, transform later.
"""

import os
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL     = os.getenv("API_BASE_URL", "https://fakestoreapi.com")
RAW_DATA_DIR = os.getenv("RAW_DATA_DIR", "data/raw")
API_TIMEOUT  = int(os.getenv("API_TIMEOUT", 10))
API_RETRIES  = int(os.getenv("API_RETRIES", 3))

ENDPOINTS = ["products", "users", "carts"]

# ── Logger ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("ingestion.fetcher")


# ── Core Functions ────────────────────────────────────────────────────────────

def fetch_endpoint(endpoint: str, retries: int = API_RETRIES) -> list:
    """
    Fetch all records from a single API endpoint.

    Uses exponential backoff: waits 2s, 4s, 8s between retries.
    This is standard practice to avoid hammering a failing API.

    Args:
        endpoint: e.g. "products", "users", "carts"
        retries:  number of attempts before raising

    Returns:
        List of raw records (dicts)

    Raises:
        RuntimeError: if all retry attempts fail
    """
    url = f"{BASE_URL}/{endpoint}"

    for attempt in range(1, retries + 1):
        try:
            log.info(f"Fetching {url}  (attempt {attempt}/{retries})")
            start = time.time()

            response = requests.get(url, timeout=API_TIMEOUT)
            response.raise_for_status()   # raises on 4xx / 5xx

            records  = response.json()
            elapsed  = round(time.time() - start, 2)

            log.info(f"  OK — {len(records)} records in {elapsed}s")
            return records

        except requests.exceptions.Timeout:
            log.warning(f"  Timeout on attempt {attempt}")
        except requests.exceptions.HTTPError as e:
            log.warning(f"  HTTP {e.response.status_code} on attempt {attempt}")
        except requests.exceptions.RequestException as e:
            log.warning(f"  Request error on attempt {attempt}: {e}")

        if attempt < retries:
            wait = 2 ** attempt          # 2s, 4s, 8s …
            log.info(f"  Waiting {wait}s before retry…")
            time.sleep(wait)

    raise RuntimeError(
        f"All {retries} attempts failed for endpoint '{endpoint}'"
    )


def build_filepath(endpoint: str, run_ts: datetime) -> str:
    """
    Build a partitioned file path for the raw landing zone.

    Pattern: data/raw/<endpoint>/<YYYY-MM-DD>/<endpoint>_<HHMMSS>.json

    Why partition by date?
      - Makes backfill and debugging easy
      - Mirrors how S3/GCS is typically organized in production
      - Enables incremental loads — only process new partitions
    """
    date_partition = run_ts.strftime("%Y-%m-%d")
    time_suffix    = run_ts.strftime("%H%M%S")
    folder = os.path.join(RAW_DATA_DIR, endpoint, date_partition)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{endpoint}_{time_suffix}.json")


def save_raw(endpoint: str, records: list, run_ts: datetime) -> str:
    """
    Persist raw records as JSON with metadata envelope.

    The _metadata block is key in production:
      - Lets you audit exactly when data arrived
      - Records source URL in case it changes later
      - Stores record count for quick sanity checks without parsing data
    """
    filepath = build_filepath(endpoint, run_ts)

    payload = {
        "_metadata": {
            "endpoint":     endpoint,
            "source_url":   f"{BASE_URL}/{endpoint}",
            "ingested_at":  run_ts.isoformat(),
            "record_count": len(records),
        },
        "data": records,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    log.info(f"  Saved → {filepath}  ({len(records)} records)")
    return filepath


def run_ingestion(endpoints: Optional[list] = None) -> dict:
    """
    Main ingestion job — pulls all endpoints and lands raw data.

    Returns a summary dict useful for Airflow XComs and alerting.
    """
    targets   = endpoints or ENDPOINTS
    run_ts    = datetime.now(timezone.utc)
    job_start = time.time()

    log.info("=" * 55)
    log.info(f"Ingestion run started  —  {run_ts.isoformat()}")
    log.info(f"Endpoints: {targets}")
    log.info("=" * 55)

    summary       = {}
    total_records = 0

    for endpoint in targets:
        try:
            records  = fetch_endpoint(endpoint)
            filepath = save_raw(endpoint, records, run_ts)
            summary[endpoint] = {"status": "success", "records": len(records), "path": filepath}
            total_records += len(records)
        except RuntimeError as e:
            log.error(f"FAILED to ingest '{endpoint}': {e}")
            summary[endpoint] = {"status": "failed", "error": str(e)}

    elapsed = round(time.time() - job_start, 2)
    log.info("=" * 55)
    log.info(f"Ingestion complete — {total_records} records in {elapsed}s")
    for ep, r in summary.items():
        if r["status"] == "success":
            log.info(f"  {ep:12s} {r['records']:>4} records → {r['path']}")
        else:
            log.error(f"  {ep:12s} FAILED — {r['error']}")
    log.info("=" * 55)

    return summary


if __name__ == "__main__":
    run_ingestion()