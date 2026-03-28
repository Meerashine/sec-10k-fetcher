"""CLI entry point for the SEC 10-K fetcher.

Usage:
    python -m sec_fetcher
"""

from __future__ import annotations

import logging
import sys
from typing import List

from playwright.sync_api import sync_playwright

from sec_fetcher.client import SecClient
from sec_fetcher.config import (
    COMPANIES,
    DEFAULT_OUTPUT_DIR,
    MANIFEST_FILENAME,
    USER_AGENT,
    WEBHOOK_URL,
)
from sec_fetcher.manifest import Manifest
from sec_fetcher.models import FilingResult
from sec_fetcher.notifier import notify_missing_filings
from sec_fetcher.pipeline import process_company

log = logging.getLogger(__name__)


def main() -> None:
    output_dir = DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / MANIFEST_FILENAME
    manifest = Manifest.load(manifest_path)

    with SecClient(USER_AGENT) as client:
        ticker_map = client.load_ticker_map()

        # Resolve CIKs up-front so we fail fast on bad tickers.
        resolved = []
        for company_name, ticker in COMPANIES.items():
            cik = ticker_map.get(ticker.upper())
            if cik is None:
                log.error(
                    "Ticker %s not found — skipping %s",
                    ticker,
                    company_name,
                )
                continue
            resolved.append((company_name, ticker, cik))

        results: List[FilingResult] = []

        # Reuse one browser for all renders — startup is expensive.
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                for name, ticker, cik in resolved:
                    log.info("Processing %s %s", name, ticker)
                    result = process_company(
                        client,
                        browser,
                        name,
                        ticker,
                        cik,
                        output_dir,
                        manifest,
                    )
                    results.append(result)
            finally:
                browser.close()

    manifest.save(manifest_path)

    _print_summary(results)


def _print_summary(results: List[FilingResult]) -> None:
    ok = [r for r in results if r.status == "ok"]
    skipped = [r for r in results if r.status == "skipped"]
    failed = [r for r in results if r.status == "error"]

    log.info(
        "Done: %d fetched, %d skipped, %d failed",
        len(ok),
        len(skipped),
        len(failed),
    )
    for r in failed:
        log.error("  FAILED  %s: %s", r.company, r.error)

    # Check: every company in config should have a result that isn't "error".
    expected = set(COMPANIES.keys())
    succeeded = {r.company for r in results if r.status in ("ok", "skipped")}
    missing = sorted(expected - succeeded)

    if missing:
        log.error("Missing filings for: %s", ", ".join(missing))
        notify_missing_filings(WEBHOOK_URL, missing)

    if failed:
        sys.exit(1)
