"""Main SEC client module.
"""
from __future__ import annotations

import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sec_fetcher.config import REQUEST_DELAY_SECONDS
from sec_fetcher.models import Filing

log = logging.getLogger(__name__)

BLOCK_MARKERS = [
    "Your Request Originates from an Undeclared Automated Tool",
    "Please declare your traffic",
    "SEC reserves the right to limit requests",
]


class SecClient:
    """Thin HTTP wrapper around the SEC EDGAR APIs."""

    TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

    def __init__(self, user_agent: str) -> None:
        self._delay = REQUEST_DELAY_SECONDS
        self._session = requests.Session()
        self._session.headers["User-Agent"] = user_agent

        retry = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retry))

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> SecClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _get_json(self, url: str) -> dict:
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        time.sleep(self._delay)
        return resp.json()

    def _get_text(self, url: str) -> str:
        resp = self._session.get(url, timeout=60)
        resp.raise_for_status()
        time.sleep(self._delay)
        return resp.text

    # API call methods:

    def load_ticker_map(self) -> dict[str, str]:
        # We need to resolve tickers to CIKs to find filings.
        log.info("Loading SEC company tickers")
        data = self._get_json(self.TICKERS_URL)
        return {
            row["ticker"].upper(): str(row["cik_str"]).zfill(10)
            for row in data.values()
        }

    def get_latest_10k(
        self, company_name: str, ticker: str, cik_padded: str,
    ) -> Filing:
        # find the latest 10-K filing for one company.
        url = self.SUBMISSIONS_URL.format(cik=cik_padded)
        value = self._get_json(url)
        recent_fillings = value["filings"]["recent"]
        # each key a list of values like form: ["10-K", "8-K", ...],
        # accessionNumber: etc..
        keys = ["accessionNumber", "filingDate", "form",
                "primaryDocument", "reportDate"]
        # converting into list of dicts for easier processing
        rows = [
            {k: recent_fillings[k][i] for k in keys}
            for i in range(len(recent_fillings["form"]))
        ]

        latest = next(
            (r for r in rows if r["form"] == "10-K"), None,
        )
        if latest is None:
            raise LookupError(
                f"No 10-K in recent filings for {company_name}"
            )

        return Filing(
            company_name=company_name,
            ticker=ticker,
            cik_padded=cik_padded,
            accession_number=latest["accessionNumber"],
            filing_date=latest["filingDate"],
            primary_document=latest["primaryDocument"],
            form=latest["form"],
        )

    def download_filing_html(self, filing: Filing) -> str:
        # download the filing's primary document HTML
        html = self._get_text(filing.filing_url)

        if any(m in html for m in BLOCK_MARKERS):
            raise RuntimeError(
                f"SEC blocked: {filing.company_name} "
                f"({filing.filing_url})"
            )

        # Inject <base href> to resolve broken images.
        base = filing.filing_url.rsplit("/", 1)[0] + "/"
        tag = f'<base href="{base}">'
        if "<head>" in html:
            html = html.replace("<head>", f"<head>{tag}", 1)
        elif "<html>" in html:
            html = html.replace(
                "<html>", f"<html><head>{tag}</head>", 1,
            )
        return html
