"""
validator.py — Phase 1: Data Quality Layer
==========================================
Responsibilities:
  - Schema validation  (required fields present, correct types)
  - Null / empty checks
  - Business rule checks  (price > 0, rating in range, etc.)
  - Return a structured quality report per endpoint

Industry pattern:
  Run validation immediately after ingestion, before any transform.
  Never silently drop bad rows — log them, count them, alert on them.
  A pipeline that swallows bad data is worse than one that fails loudly.
"""

import logging
from typing import Any

log = logging.getLogger("ingestion.validator")


# ── Schema Definitions ────────────────────────────────────────────────────────
# Each schema maps field name → expected Python type.
# This is a lightweight alternative to Pydantic/Great Expectations
# that's easy to understand and extend.

PRODUCT_SCHEMA = {
    "id":          int,
    "title":       str,
    "price":       float,
    "description": str,
    "category":    str,
    "image":       str,
}

USER_SCHEMA = {
    "id":       int,
    "email":    str,
    "username": str,
    "password": str,
}

CART_SCHEMA = {
    "id":     int,
    "userId": int,
    "date":   str,
}

SCHEMAS = {
    "products": PRODUCT_SCHEMA,
    "users":    USER_SCHEMA,
    "carts":    CART_SCHEMA,
}


# ── Validation Helpers ────────────────────────────────────────────────────────

def _check_field(record: dict, field: str, expected_type: type, row_idx: int) -> list[str]:
    """Check a single field on a single record. Returns list of issue strings."""
    issues = []
    value  = record.get(field)

    if value is None:
        issues.append(f"row {row_idx}: '{field}' is null/missing")
    elif not isinstance(value, expected_type):
        # FakeStore returns prices as float but sometimes int — allow both numeric
        if expected_type is float and isinstance(value, int):
            pass   # int is acceptable where float expected
        else:
            issues.append(
                f"row {row_idx}: '{field}' expected {expected_type.__name__}, "
                f"got {type(value).__name__} (value={repr(value)})"
            )

    return issues


def _check_business_rules(record: dict, endpoint: str, row_idx: int) -> list[str]:
    """
    Endpoint-specific business rules beyond basic type checks.
    These catch domain-logic errors that schema checks miss.
    """
    issues = []

    if endpoint == "products":
        price = record.get("price")
        if price is not None and price < 0:
            issues.append(f"row {row_idx}: 'price' is negative ({price})")

        rating = record.get("rating", {})
        rate   = rating.get("rate") if isinstance(rating, dict) else None
        count  = rating.get("count") if isinstance(rating, dict) else None

        if rate is not None and not (0.0 <= rate <= 5.0):
            issues.append(f"row {row_idx}: 'rating.rate' out of range ({rate})")
        if count is not None and count < 0:
            issues.append(f"row {row_idx}: 'rating.count' is negative ({count})")

    if endpoint == "users":
        email = record.get("email", "")
        if email and "@" not in email:
            issues.append(f"row {row_idx}: 'email' looks invalid ({email})")

    if endpoint == "carts":
        products = record.get("products", [])
        if not isinstance(products, list) or len(products) == 0:
            issues.append(f"row {row_idx}: cart has no products")
        else:
            for i, item in enumerate(products):
                qty = item.get("quantity", 0)
                if qty <= 0:
                    issues.append(f"row {row_idx}: cart item {i} has quantity={qty}")

    return issues


# ── Main Validator ────────────────────────────────────────────────────────────

def validate(endpoint: str, records: list) -> dict:
    """
    Run all quality checks on a list of ingested records.

    Returns a structured report:
    {
        "endpoint":   "products",
        "total":      20,
        "passed":     19,
        "failed":     1,
        "pass_rate":  95.0,
        "issues":     ["row 4: 'price' is negative (-1.0)"],
    }

    In production this report is:
      - Logged to your monitoring system
      - Stored alongside the raw file for auditing
      - Used to trigger alerts if pass_rate drops below a threshold
    """
    schema = SCHEMAS.get(endpoint)
    if not schema:
        log.warning(f"No schema defined for endpoint '{endpoint}' — skipping validation")
        return {"endpoint": endpoint, "total": len(records), "skipped": True}

    all_issues: list[str] = []
    failed_rows: set[int] = set()

    for idx, record in enumerate(records):
        row_issues: list[str] = []

        # 1. Schema checks
        for field, expected_type in schema.items():
            row_issues.extend(_check_field(record, field, expected_type, idx))

        # 2. Business rule checks
        row_issues.extend(_check_business_rules(record, endpoint, idx))

        if row_issues:
            failed_rows.add(idx)
            all_issues.extend(row_issues)

    total     = len(records)
    failed    = len(failed_rows)
    passed    = total - failed
    pass_rate = round((passed / total) * 100, 1) if total > 0 else 0.0

    report = {
        "endpoint":  endpoint,
        "total":     total,
        "passed":    passed,
        "failed":    failed,
        "pass_rate": pass_rate,
        "issues":    all_issues,
    }

    # Log summary
    level = logging.INFO if pass_rate >= 95.0 else logging.WARNING
    log.log(level, f"Validation [{endpoint}] — {passed}/{total} passed ({pass_rate}%)")

    for issue in all_issues:
        log.warning(f"  ISSUE: {issue}")

    return report


def validate_all(ingestion_summary: dict) -> dict:
    """
    Run validation for every endpoint in an ingestion summary.
    Reads each saved JSON file and validates its data block.

    Args:
        ingestion_summary: the dict returned by run_ingestion()

    Returns:
        { "products": <report>, "users": <report>, "carts": <report> }
    """
    import json

    validation_results = {}

    for endpoint, result in ingestion_summary.items():
        if result.get("status") != "success":
            log.warning(f"Skipping validation for '{endpoint}' — ingestion failed")
            continue

        filepath = result["path"]
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
            records = payload.get("data", [])
            validation_results[endpoint] = validate(endpoint, records)
        except Exception as e:
            log.error(f"Could not read file for validation [{endpoint}]: {e}")
            validation_results[endpoint] = {"endpoint": endpoint, "error": str(e)}

    return validation_results