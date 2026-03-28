from __future__ import annotations

import logging
from pathlib import Path

from playwright.sync_api import Browser

from sec_fetcher.client import SecClient
from sec_fetcher.config import WEBHOOK_URL
from sec_fetcher.manifest import Manifest
from sec_fetcher.models import FilingResult
from sec_fetcher.notifier import notify_new_filing
from sec_fetcher.renderer import render_pdf, save_html

log = logging.getLogger(__name__)


def process_company(
    client: SecClient,
    browser: Browser,
    company_name: str,
    ticker: str,
    cik_padded: str,
    output_dir: Path,
    manifest: Manifest,
) -> FilingResult:
    """Fetch and convert one company's 10-K.

    made it like alsways returns ``FilingResult``.so other
    comanies can be processed even if one fails.
    """
    try:
        filing = client.get_latest_10k(
            company_name, ticker, cik_padded,
        )

        if manifest.contains(filing.accession_number):
            log.info(
                "  Already fetched (accession %s), skipping",
                filing.accession_number,
            )
            return FilingResult(
                company=company_name,
                ticker=ticker,
                status="skipped",
            )

        html = client.download_filing_html(filing)

        html_path = output_dir / filing.html_filename
        save_html(html, html_path)

        pdf_path = output_dir / filing.pdf_filename
        render_pdf(browser, html, pdf_path)

        manifest.record(filing)
        notify_new_filing(WEBHOOK_URL, filing, str(pdf_path))

        return FilingResult(
            company=company_name,
            ticker=ticker,
            status="ok",
            filing=filing,
            pdf_path=str(pdf_path),
        )

    except Exception as exc:
        log.error("  Failed: %s", exc)
        return FilingResult(
            company=company_name,
            ticker=ticker,
            status="error",
            error=str(exc),
        )
