"""Vertt API – calculated ride offers (PRD-7).

An offer for a ride from position A to position B at a pickup time:
distance, ride time and street route from Valhalla, price with the Vertt tariff,
CO₂ with a car drawn from config/car_pool.yaml.

Try it locally:  .venv\\Scripts\\python.exe -m src.vertt
"""
from __future__ import annotations

import hashlib
import math
import random
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import httpx
import polyline
import yaml

API_VERSION = "1"
ROOT = Path(__file__).resolve().parents[1]
VALHALLA_URL = "https://valhalla1.openstreetmap.de/route"

# Vertt tariff, service class "Standard" – the same everywhere in Switzerland (PRD-7)
INITIAL_CHF = 3.00
PER_KM_CHF = 1.80
PER_MIN_CHF = 0.30
MIN_PRICE_CHF = 10.00
FACTOR = 1.0

MIN_DISTANCE_KM = 1.0                      # below this a walk is the right answer (PRD-8)
SWITZERLAND = (45.80, 47.84, 5.95, 10.50)  # rough box: lat min/max, lon min/max


class NotServed(Exception):
    """Vertt cannot offer this ride – the answer is "not served", never a guessed price."""


def tariff(km: float, minutes: float) -> float:
    """Price in CHF, exact to the centime (the booking app rounds to 0.05)."""
    return round(max(MIN_PRICE_CHF, INITIAL_CHF + PER_KM_CHF * km + PER_MIN_CHF * minutes) * FACTOR, 2)


@lru_cache(maxsize=1)
def car_pool() -> list[dict]:
    with open(ROOT / "config" / "car_pool.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["cars"]


def straight_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    return 2 * 6371 * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))


def in_switzerland(p: tuple[float, float]) -> bool:
    lat_min, lat_max, lon_min, lon_max = SWITZERLAND
    return lat_min <= p[0] <= lat_max and lon_min <= p[1] <= lon_max


_routes: dict = {}


def valhalla_route(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float, list]:
    """(km, minutes, route points) from Valhalla. Answers are kept, so a repeated search costs no call."""
    key = (round(a[0], 5), round(a[1], 5), round(b[0], 5), round(b[1], 5))
    if key not in _routes:
        try:
            r = httpx.post(VALHALLA_URL, timeout=20, json={
                "locations": [{"lat": a[0], "lon": a[1]}, {"lat": b[0], "lon": b[1]}], "costing": "auto"})
            r.raise_for_status()
            trip = r.json()["trip"]
        except (httpx.HTTPError, KeyError, ValueError) as e:
            raise NotServed("no_route") from e
        points = polyline.decode(trip["legs"][0]["shape"], 6)      # Valhalla uses precision 6
        _routes[key] = (trip["summary"]["length"], trip["summary"]["time"] / 60, points)
    return _routes[key]


def offer_id(start, dest, pickup: datetime) -> str:
    raw = f"{start[0]:.5f},{start[1]:.5f}|{dest[0]:.5f},{dest[1]:.5f}|{pickup.isoformat(timespec='minutes')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def calculate_offer(start, dest, pickup: datetime, route=valhalla_route) -> dict:
    """The Vertt offer for one ride. Raises NotServed if Vertt cannot offer it."""
    start, dest = tuple(start), tuple(dest)
    if not (in_switzerland(start) and in_switzerland(dest)):
        raise NotServed("outside_switzerland")
    if straight_km(start, dest) < MIN_DISTANCE_KM:
        raise NotServed("too_short")
    km, minutes, points = route(start, dest)
    oid = offer_id(start, dest, pickup)
    car = random.Random(oid).choice(car_pool())                 # "random", but the same for the same offer
    return {
        "version": API_VERSION,
        "status": "offer",
        "offer_id": oid,
        "pickup_time": pickup.isoformat(timespec="minutes"),
        "distance_km": round(km, 3),
        "ride_time_min": round(minutes, 1),
        "price_chf": tariff(km, minutes),
        "currency": "CHF",
        "factor": FACTOR,
        "car_category": "Vertt",
        "car": {k: car[k] for k in ("make", "model", "year", "co2_g_per_km")},
        "co2_kg": round(km * car["co2_g_per_km"] / 1000, 3),
        "route": [[round(lat, 5), round(lon, 5)] for lat, lon in points],
        "assumptions": {"calculated": True, "tariff": "Vertt standard, same everywhere", "factor": FACTOR,
                        "car": "drawn from the car pool"},
    }


def handle_request(payload: dict, secret: str | None, expected_secret: str | None, route=valhalla_route) -> tuple[int, dict]:
    """HTTP-independent entrance: (status code, JSON answer). Used by api/vertt/offer.py."""
    if not expected_secret or secret != expected_secret:
        return 403, {"version": API_VERSION, "status": "not_allowed"}
    try:
        start = (float(payload["start"]["lat"]), float(payload["start"]["lon"]))
        dest = (float(payload["destination"]["lat"]), float(payload["destination"]["lon"]))
        pickup = datetime.fromisoformat(payload["pickup_time"])
    except (KeyError, TypeError, ValueError):
        return 400, {"version": API_VERSION, "status": "invalid_request",
                     "expected": {"start": {"lat": 0, "lon": 0}, "destination": {"lat": 0, "lon": 0},
                                  "pickup_time": "2026-10-13T08:05+02:00"}}
    try:
        return 200, calculate_offer(start, dest, pickup, route)
    except NotServed as e:
        return 200, {"version": API_VERSION, "status": "not_served", "reason": str(e)}


if __name__ == "__main__":                     # quick local try: Wettswil am Albis -> Zürich HB
    o = calculate_offer((47.3416, 8.4708), (47.37818, 8.54021), datetime.fromisoformat("2026-10-13T08:05+02:00"))
    print({k: v for k, v in o.items() if k != "route"}, f"\nroute: {len(o['route'])} points")
