from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from playwright.sync_api import Browser

log = logging.getLogger(__name__)


def save_html(html: str, html_path: Path) -> None:
    """Persist the raw filing HTML for downstream ML/NLP use."""
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    log.info("  HTML saved: %s", html_path.name)


def render_pdf(
    browser: Browser,
    html: str,
    pdf_path: Path,
) -> None:
    """Render HTML string to a paginated A4 PDF.

    Writes HTML to a temporary file (needed as Playwright can
    navigate to it and resolve the HTML references for assets),
    then deletes it after rendering.
    """
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8",
    ) as tmp:
        tmp.write(html)
        tmp_path = Path(tmp.name)

    page = browser.new_page()
    try:
        page.goto(
            tmp_path.resolve().as_uri(),
            wait_until="load",
            timeout=120_000,
        )
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={
                "top": "16mm",
                "right": "12mm",
                "bottom": "16mm",
                "left": "12mm",
            },
        )
        log.info("  PDF saved : %s", pdf_path.name)
    finally:
        page.close()
        tmp_path.unlink(missing_ok=True)
