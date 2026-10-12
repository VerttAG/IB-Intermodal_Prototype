"""Vercel function: POST /api/trips – trip offers for the booking app (PRD-8, docs/api/trip-offers.md).

Called by the booking app in the browser (behind the password gate); the partner keys stay on the server.
"""
import datetime as dt
import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # repo root, so that "src" can be imported
from src.engine import API_VERSION, SearchError, search  # noqa: E402


def handle_request(payload: dict) -> tuple[int, dict]:
    try:
        start = (float(payload["start"]["lat"]), float(payload["start"]["lon"]))
        dest = (float(payload["destination"]["lat"]), float(payload["destination"]["lon"]))
        departure = dt.datetime.fromisoformat(payload["departure"])
        if departure.tzinfo is None:
            raise ValueError("departure needs a time zone")
    except (KeyError, TypeError, ValueError):
        return 400, {"version": API_VERSION, "status": "invalid_request",
                     "expected": {"start": {"lat": 0, "lon": 0}, "destination": {"lat": 0, "lon": 0},
                                  "departure": "2026-10-13T08:00+02:00"}}
    try:
        return 200, search(start, dest, departure)
    except SearchError as e:
        return (429 if e.status == "too_many_searches" else 400), {"version": API_VERSION, "status": e.status, "message": e.message}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            payload = {}
        status, body = handle_request(payload)
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
