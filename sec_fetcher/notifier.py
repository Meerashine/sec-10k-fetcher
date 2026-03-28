"""Webhook notifier — calls an endpoint when new filings are fetched."""

from __future__ import annotations

import logging
import requests
from datetime import datetime, timezone
from typing import Optional

from sec_fetcher.models import Filing

log = logging.getLogger(__name__)


def notify_new_filing(
    webhook_url: Optional[str],
    filing: Filing,
    pdf_path: str,
) -> None:
    """POST a JSON payload to the webhook URL.

    Silently logs and returns on failure — notification should
    never block the pipeline.
    """
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

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        log.info("  Notified Teams for: %s", filing.company_name)
    except Exception as exc:
        log.warning("  Webhook failed: %s", exc)
