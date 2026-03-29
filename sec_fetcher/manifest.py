"""JSON manifest for filing deduplication."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Set

from sec_fetcher.models import Filing


class Manifest:
    # This class tracks fetched accession numbers so re-runs skip duplicates.

    def __init__(self, seen: Set[str] | None = None) -> None:
        self._seen: Set[str] = seen or set()

    @classmethod
    def load(cls, path: Path) -> Manifest:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(set(data.get("fetched", [])))
        return cls()

    def save(self, path: Path) -> None:
        path.write_text(
            json.dumps({"fetched": sorted(self._seen)}, indent=2),
            encoding="utf-8",
        )

    def contains(self, accession_number: str) -> bool:
        return accession_number in self._seen

    def record(self, filing: Filing) -> None:
        self._seen.add(filing.accession_number)
