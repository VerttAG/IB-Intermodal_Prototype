"""Booking store – where the data behind the data links lives (PRD-5).

Locally: one JSON file per booking in data/local/bookings/ (gitignored).
On Vercel this file is replaced by an online store (issue #22/#23); the rest of the code stays the same.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_ID = re.compile(r"^BK-\d{6}$")


def _folder() -> Path:
    folder = Path(os.environ.get("BOOKING_STORE_DIR", ROOT / "data" / "local" / "bookings"))
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save(record: dict) -> None:
    booking_id = record["booking"]["booking_id"]
    (_folder() / f"{booking_id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")


def load(booking_id: str) -> dict | None:
    if not _ID.match(booking_id or ""):          # only real booking IDs – never a path from outside
        return None
    f = _folder() / f"{booking_id}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
