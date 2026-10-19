"""Booking store – where the data behind the data links lives (PRD-5).

Online (Vercel): an Upstash Redis store, used as soon as its two environment variables are set
(KV_REST_API_URL / KV_REST_API_TOKEN, added by Vercel when the store is connected to the project).
Locally: one JSON file per booking in data/local/bookings/ (gitignored).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
_ID = re.compile(r"^BK-\d{6}$")


def _redis() -> tuple[str, str] | None:
    url = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
    token = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    return (url, token) if url and token else None


def _command(*args: str):
    """One Redis command over Upstash's REST interface, e.g. ("GET", "booking:BK-123456")."""
    url, token = _redis()
    r = httpx.post(url, json=list(args), headers={"Authorization": f"Bearer {token}"}, timeout=10)
    r.raise_for_status()
    return r.json()["result"]


def _folder() -> Path:
    folder = Path(os.environ.get("BOOKING_STORE_DIR", ROOT / "data" / "local" / "bookings"))
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save(record: dict) -> None:
    booking_id = record["booking"]["booking_id"]
    text = json.dumps(record, ensure_ascii=False, indent=1)
    if _redis():
        _command("SET", f"booking:{booking_id}", text)
    else:
        (_folder() / f"{booking_id}.json").write_text(text, encoding="utf-8")


def load(booking_id: str) -> dict | None:
    if not _ID.match(booking_id or ""):          # only real booking IDs – never a path or key from outside
        return None
    if _redis():
        text = _command("GET", f"booking:{booking_id}")
        return json.loads(text) if text else None
    f = _folder() / f"{booking_id}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
