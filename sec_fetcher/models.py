"""Models used for SEC filings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Filing:

    """Data model for a single SEC filing"""

    company_name: str
    ticker: str
    cik_padded: str
    accession_number: str
    filing_date: str
    primary_document: str
    form: str

    @property
    def cik_numeric(self) -> str:
        return str(int(self.cik_padded))

    @property
    def accession_no_dashes(self) -> str:
        return self.accession_number.replace("-", "")

    @property
    def filing_url(self) -> str:
        return (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{self.cik_numeric}/"
            f"{self.accession_no_dashes}/"
            f"{self.primary_document}"
        )

    @property
    def html_filename(self) -> str:
        safe = self.company_name.replace(" ", "_")
        return f"{safe}_{self.ticker}_{self.filing_date}_{self.form}.html"

    @property
    def pdf_filename(self) -> str:
        safe = self.company_name.replace(" ", "_")
        return f"{safe}_{self.ticker}_{self.filing_date}_{self.form}.pdf"


@dataclass
class FilingResult:
    """Outcome data model after processing a company's filing."""

    company: str
    ticker: str
    status: str  # "ok", "skipped", "error"
    filing: Optional[Filing] = None
    pdf_path: Optional[str] = None
    error: Optional[str] = None
