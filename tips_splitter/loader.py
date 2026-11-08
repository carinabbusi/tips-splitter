"""Read tip entries from a CSV file.

Expected columns: date,amount,workers
- date: YYYY-MM-DD
- amount: euros, e.g. 42.50
- workers: names separated by ';', e.g. Alex;Bia;Caio
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from .splitter import TipEntry, TipSplitError

REQUIRED_COLUMNS = {"date", "amount", "workers"}


def load_entries(path: str | Path) -> list[TipEntry]:
    entries: list[TipEntry] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise TipSplitError(f"CSV is missing columns: {', '.join(sorted(missing))}")

        for line_number, row in enumerate(reader, start=2):
            try:
                day = date.fromisoformat(row["date"].strip())
            except ValueError as exc:
                raise TipSplitError(f"Line {line_number}: invalid date {row['date']!r}") from exc
            workers = tuple(w for w in row["workers"].split(";") if w.strip())
            entries.append(TipEntry(day=day, amount=Decimal(row["amount"].strip()), workers=workers))
    return entries
