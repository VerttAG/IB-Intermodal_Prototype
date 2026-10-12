"""Local server for the app – no Vercel needed.

    .venv\\Scripts\\python.exe dev_server.py      then open http://localhost:8000

Serves app/ and passes /api/... to the same entrances Vercel uses (api/trips.py, api/bookings.py).
Keys come from .env; bookings are stored in data/local/bookings/ (gitignored).
"""
import importlib.util
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app"
PORT = 8000
load_dotenv(ROOT / ".env")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "api" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


trips, bookings = _load("trips"), _load("bookings")


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, body):
        data = json.dumps(body, ensure_ascii=False, indent=1).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/bookings":
            return self._json(*bookings.handle_get(parse_qs(url.query)))
        file = (APP / (url.path.lstrip("/") or "index.html")).resolve()
        if APP not in file.parents and file != APP / "index.html" or not file.is_file():
            self.send_error(404)
            return
        data = file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", (mimetypes.guess_type(file.name)[0] or "application/octet-stream") + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            payload = {}
        path = urlparse(self.path).path
        if path == "/api/trips":
            return self._json(*trips.handle_request(payload))
        if path == "/api/bookings":
            return self._json(*bookings.handle_post(payload))
        self.send_error(404)


if __name__ == "__main__":
    print(f"App running on http://localhost:{PORT}  (stop with Ctrl+C)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
