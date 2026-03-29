"""Notifier module for sending updates about SEC filing processing to other
    teams or systems via webhooks."""

from __future__ import annotations

import logging
import requests
from datetime import datetime, timezone
from typing import Optional

from sec_fetcher.models import Filing

log = logging.getLogger(__name__)


def _post(webhook_url: str, payload: dict, context: str) -> None:
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        log.info("  Webhook sent (%s)", context)
    except Exception as exc:
        log.warning("  Webhook failed (%s): %s", context, exc)


def notify_new_filing(
    webhook_url: Optional[str],
    filing: Filing,
    pdf_path: str,
) -> None:

    if not webhook_url:
        return

    payload = {
        "event": "filing_created",
        "company": filing.company_name,
        "ticker": filing.ticker,
        "form": filing.form,
        "filing_date": filing.filing_date,
        "accession_number": filing.accession_number,
        "pdf_path": pdf_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _post(webhook_url, payload, context=f"new-filing:{filing.company_name}")


def notify_missing_filings(
    webhook_url: Optional[str],
    missing: list[str],
) -> None:
    if not webhook_url or not missing:
        return

    payload = {
        "event": "missing_filings",
        "companies": missing,
        "message": f"No 10-K filing found for: {', '.join(missing)}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _post(webhook_url, payload, context="missing-filings")


def notify_run_failure(
    webhook_url: Optional[str],
    error: str,
) -> None:
    if not webhook_url:
        return

    payload = {
        "event": "run_failed",
        "message": f"Scheduled SEC fetch failed: {error}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _post(webhook_url, payload, context="run-failure")
