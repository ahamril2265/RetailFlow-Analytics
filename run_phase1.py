"""
run_phase1.py — Phase 1 entry point
====================================
Runs the full ingestion + validation pipeline.
Uses mock data when the real API is unavailable (e.g. local dev, CI).
In Phase 2, Airflow replaces this with a proper scheduled DAG.
"""

import json
import os
from datetime import datetime, timezone
from ingestion.fetcher   import save_raw, ENDPOINTS
from ingestion.validator import validate_all
from mock_data import MOCK_PRODUCTS, MOCK_USERS, MOCK_CARTS

MOCK_RESPONSES = {
    "products": MOCK_PRODUCTS,
    "users":    MOCK_USERS,
    "carts":    MOCK_CARTS,
}


def run_mock_ingestion() -> dict:
    """Ingest from mock data instead of live API (for local dev)."""
    run_ts  = datetime.now(timezone.utc)
    summary = {}
    print(f"  Run timestamp: {run_ts.isoformat()}")

    for endpoint in ENDPOINTS:
        records  = MOCK_RESPONSES[endpoint]
        filepath = save_raw(endpoint, records, run_ts)
        summary[endpoint] = {"status": "success", "records": len(records), "path": filepath}

    return summary


def print_report(summary: dict, validation: dict):
    total_ingested = sum(r.get("records", 0) for r in summary.values() if r.get("status") == "success")

    print(f"\n{'Endpoint':<14} {'Ingested':>9} {'Valid':>6} {'Failed':>7} {'Pass rate':>10}  Issues")
    print("─" * 70)

    for endpoint in ENDPOINTS:
        ing = summary.get(endpoint, {})
        val = validation.get(endpoint, {})

        ingested  = ing.get("records",  "—")
        passed    = val.get("passed",   "—")
        failed    = val.get("failed",   "—")
        pass_rate = val.get("pass_rate","—")
        n_issues  = len(val.get("issues", []))
        issue_str = f"{n_issues} issue(s)" if n_issues else "none"

        print(f"  {endpoint:<12} {ingested:>9} {passed:>6} {failed:>7} {str(pass_rate)+('%' if pass_rate != '—' else ''):>10}  {issue_str}")

    print("─" * 70)
    print(f"  {'TOTAL':<12} {total_ingested:>9}\n")

    print("  Validation issues found:")
    for endpoint, val in validation.items():
        for issue in val.get("issues", []):
            print(f"    [{endpoint}] {issue}")

    print(f"\n  Raw files saved to: data/raw/")
    print(f"  Resume metric: ingested {total_ingested} records across {len(ENDPOINTS)} endpoints\n")


def main():
    print("\n══════════════════════════════════════════════════════")
    print("  PHASE 1 — Data Ingestion & Validation")
    print("══════════════════════════════════════════════════════")

    print("\n── STEP 1: INGESTION ──────────────────────────────────")
    summary = run_mock_ingestion()

    print("\n── STEP 2: VALIDATION ─────────────────────────────────")
    validation = validate_all(summary)

    print("\n── PHASE 1 REPORT ─────────────────────────────────────")
    print_report(summary, validation)


if __name__ == "__main__":
    main()