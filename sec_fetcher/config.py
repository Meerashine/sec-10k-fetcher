"""Centralised configuration constants."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

# SEC requires a real name + email in User-Agent.
USER_AGENT = "Meerashine Joe meera@example.com"

DEFAULT_OUTPUT_DIR = Path("sec_10k_pdfs")
MANIFEST_FILENAME = "manifest.json"

# SEC asks for <=10 req/s; we stay well under.
REQUEST_DELAY_SECONDS = 1.0

COMPANIES: Dict[str, str] = {
    "Apple": "AAPL",
    "Meta": "META",
    "Alphabet": "GOOGL",
    "Amazon": "AMZN",
    "Netflix": "NFLX",
    "Goldman Sachs": "GS",
}

# Webhook URL to notify when a new filing is fetched.
# Right now NONE but this can be a teams URL or slack.
WEBHOOK_URL: str | None = None
