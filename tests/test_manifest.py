"""Test manifest deduplication logic.
more testcases can be added with more time"""

import json
from pathlib import Path

from sec_fetcher.manifest import Manifest
from sec_fetcher.models import Filing


def _make_filing(accession: str) -> Filing:
    return Filing(
        company_name="Apple",
        ticker="AAPL",
        cik_padded="0000320193",
        accession_number=accession,
        filing_date="2025-10-31",
        primary_document="doc.htm",
        form="10-K",
    )


def test_manifest_skips_duplicate_accession(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"

    # Start with an empty manifest
    manifest = Manifest.load(manifest_path)

    filing = _make_filing("0000320193-25-000106")

    # First time — not seen yet
    assert not manifest.contains(filing.accession_number)

    # Record the filing
    manifest.record(filing)
    manifest.save(manifest_path)

    # Now it should be recognised as a duplicate
    assert manifest.contains(filing.accession_number)

    # Reload from disk to prove persistence
    reloaded = Manifest.load(manifest_path)
    assert reloaded.contains(filing.accession_number)

    # Verify the saved JSON structure
    data = json.loads(manifest_path.read_text())
    assert "0000320193-25-000106" in data["fetched"]
