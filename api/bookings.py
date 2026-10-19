"""Vercel function: /api/bookings – book, cancel and read the data link (PRD-4, PRD-5, issue #22).

POST {"action": "book", "trip": {...}, "system", "travelcard", "promo_percent", "payment_method", "login_method"}
POST {"action": "cancel", "booking_id": "BK-123456"}
GET  /api/bookings?id=BK-123456            -> the data link content
"""
import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # repo root, so that "src" can be imported
from src import settlement, store  # noqa: E402

VERSION = "1"


def handle_get(query: dict) -> tuple[int, dict]:
    record = store.load((query.get("id") or [""])[0])
    return (200, record) if record else (404, {"version": VERSION, "status": "not_found"})


def handle_post(payload: dict) -> tuple[int, dict]:
    action = payload.get("action")
    if action == "book":
        try:
            record = settlement.book(payload["trip"], payload["system"], payload["travelcard"], int(payload.get("promo_percent", 0)),
                                     payload["payment_method"], payload["login_method"])
        except (KeyError, TypeError, ValueError, StopIteration) as e:
            return 400, {"version": VERSION, "status": "invalid_request", "message": str(e)}
        while store.load(record["booking"]["booking_id"]):     # booking numbers are unique (PRD-5 edge case)
            record = settlement.book(payload["trip"], payload["system"], payload["travelcard"], int(payload.get("promo_percent", 0)),
                                     payload["payment_method"], payload["login_method"])
        store.save(record)                     # the booking exists from the click on "Pay" (PRD-3)
        return 200, record
    if action == "cancel":
        record = store.load(payload.get("booking_id", ""))
        if not record:
            return 404, {"version": VERSION, "status": "not_found"}
        try:
            record = settlement.cancel(record)
        except settlement.AlreadyCancelled:
            return 409, {"version": VERSION, "status": "already_cancelled"}
        store.save(record)                     # same link, updated content (PRD-5 AC-9)
        return 200, record
    return 400, {"version": VERSION, "status": "invalid_request", "message": "action must be 'book' or 'cancel'"}


class handler(BaseHTTPRequestHandler):
    def _send(self, status, body):
        data = json.dumps(body, ensure_ascii=False, indent=1).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(*handle_get(parse_qs(urlparse(self.path).query)))

    def do_POST(self):
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            payload = {}
        self._send(*handle_post(payload))
