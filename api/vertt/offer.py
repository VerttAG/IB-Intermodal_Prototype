"""Vercel function: POST /api/vertt/offer – Vertt ride offer (PRD-7).

Only our own server may call it: the header X-Vertt-Secret must match VERTT_API_SECRET.
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # repo root, so that "src" can be imported
from src.vertt import handle_request  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            payload = {}
        status, body = handle_request(payload, self.headers.get("X-Vertt-Secret"), os.environ.get("VERTT_API_SECRET"))
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
