"""Trip engine – door-to-door trips calculated live (PRD-8).

search(start, destination, departure) -> answer for the booking app:
up to 3 trips labelled Fastest / Cheapest / Greenest (for each travelcard) and the two comparison cards.

Try it locally:  .venv\\Scripts\\python.exe -m src.engine
"""
from __future__ import annotations

import datetime as dt
import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

import httpx
import yaml

from src import ojp, vertt

API_VERSION = "1"
WALK_KM = 1.0                  # station within 1 km (straight line): walk instead of Vertt
HUB_RADIUS_KM = 25
MIN_TRIP_KM = 10               # below: "Trip not suitable for intermodal journey"
WAIT_START_MIN = 5             # car arrives 5 min after the chosen time
WAIT_DEST_MIN = 2              # car waits 2 min after the train arrival
HALF_FARE_CHF_PER_KM = 0.22    # price estimate if no train of the search could be priced
PAST_TOLERANCE_MIN = 5
WALK_KMH = 4.5                 # only if OJP gives no walking time
TRAVELCARDS = ("none", "half", "ga")


class SearchError(Exception):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status, self.message = status, message


# ---------- partners (replaced by fakes in the tests) ----------
def vertt_offer(a, b, pickup: dt.datetime) -> dict | None:
    """The one place where the engine asks the Vertt API (direct call in Prototype 1, PRD-7)."""
    try:
        return vertt.calculate_offer(a, b, pickup)
    except vertt.NotServed:
        return None


@dataclass
class Partners:
    vertt_offer: Callable = vertt_offer
    walk: Callable = ojp.walk
    train: Callable = ojp.train
    half_fare_price: Callable = ojp.half_fare_price
    public_transport_only: Callable = ojp.public_transport_only


# ---------- stations ----------
@lru_cache(maxsize=1)
def hubs() -> list[dict]:
    with open(vertt.ROOT / "config" / "hubs.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["hubs"]


def candidates(pos, start, dest) -> list[dict]:
    """Tier rule (PRD-8): Tier 1 always; Tier 2 / 3 only if closer than the hubs already chosen. Best = distance + detour."""
    direct = vertt.straight_km(start, dest)
    rows = []
    for h in hubs():
        p = (h["lat"], h["lon"])
        rows.append({**h, "pos": p, "dist": vertt.straight_km(pos, p),
                     "detour": vertt.straight_km(start, p) + vertt.straight_km(p, dest) - direct})
    best = lambda rs: min(rs, key=lambda r: r["dist"] + r["detour"])
    tier1 = [r for r in rows if r["tier"] == 1 and r["dist"] <= HUB_RADIUS_KM]
    chosen = [best(tier1) if tier1 else min((r for r in rows if r["tier"] == 1), key=lambda r: r["dist"])]
    for tier in (2, 3):
        near = [r for r in rows if r["tier"] == tier and r["dist"] <= HUB_RADIUS_KM]
        if near and best(near)["dist"] < min(c["dist"] for c in chosen):
            chosen.append(best(near))
    return chosen


# ---------- helpers ----------
def r05(x: float) -> float:
    return round(round(x * 20) / 20, 2)


def _iso(t: dt.datetime) -> str:
    return t.astimezone(ojp.SWISS).isoformat(timespec="minutes")


def _safe(fn, *args):
    """Partner call; a failure drops only that leg – except OJP's rate limit, which stops the search."""
    try:
        return fn(*args)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise SearchError("too_many_searches", "Too many searches, please wait a moment") from e
        return None
    except (httpx.HTTPError, KeyError, ValueError):
        return None


def _walk_leg(found, a_pos, b_pos, start: dt.datetime, frm: str, to: str) -> dict:
    if found is None:                         # OJP gave no walking time: estimate from the distance
        km = vertt.straight_km(a_pos, b_pos) * 1.3
        found = {"minutes": km / WALK_KMH * 60, "km": km, "route": [list(a_pos), list(b_pos)]}
    return {"kind": "walk", "from": frm, "to": to, "departure": start, "arrival": start + dt.timedelta(minutes=found["minutes"]),
            "minutes": round(found["minutes"], 1), "distance_km": round(found["km"], 3), "route": found["route"],
            "price_chf": 0.0, "co2_kg": 0.0}


def _vertt_leg(offer, pickup: dt.datetime, wait: int, frm: str, to: str) -> dict:
    return {"kind": "vertt", "from": frm, "to": to, "wait_min": wait, "pickup": pickup,
            "arrival": pickup + dt.timedelta(minutes=offer["ride_time_min"]), "ride_time_min": offer["ride_time_min"],
            "distance_km": offer["distance_km"], "price_chf": r05(offer["price_chf"]), "car": offer["car"],
            "co2_kg": offer["co2_kg"], "route": offer["route"], "offer_id": offer["offer_id"]}


def _train_legs(trip: dict) -> list[dict]:
    out = []
    for l in trip["legs"]:
        if l["kind"] == "train":
            out.append({"kind": "train", "line": l["line"], "from": l["from"], "to": l["to"], "departure": l["dep"],
                        "arrival": l["arr"], "platform": l["platform"], "distance_km": l["km"], "co2_kg": l["co2_kg"], "route": l["route"]})
        elif l["kind"] in ("transfer", "walk") and out:
            out.append({"kind": "transfer", "minutes": l["minutes"]})
    while out and out[-1]["kind"] == "transfer":
        out.pop()
    return out


def _train_price(half: float, card: str) -> float:
    return {"none": r05(2 * half), "half": r05(half), "ga": 0.0}[card]


def _serialise(x):
    if isinstance(x, dt.datetime):
        return _iso(x)
    if isinstance(x, dict):
        return {k: _serialise(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_serialise(v) for v in x]
    return x


# ---------- search ----------
def search(start, dest, departure: dt.datetime, now: dt.datetime | None = None, partners: Partners | None = None) -> dict:
    p = partners or Partners()
    start, dest = tuple(start), tuple(dest)
    now = now or dt.datetime.now(ojp.SWISS)
    if departure < now - dt.timedelta(minutes=PAST_TOLERANCE_MIN):
        raise SearchError("past_time", "Please choose a time in the future")
    base = {"version": API_VERSION, "departure": _iso(departure)}
    if vertt.straight_km(start, dest) < MIN_TRIP_KM:
        return {**base, "status": "not_suitable", "message": "Trip not suitable for intermodal journey", "trips": []}

    cs, cd = candidates(start, start, dest), candidates(dest, start, dest)
    with ThreadPoolExecutor(max_workers=16) as pool:
        # round 1: first legs and the comparison cards
        def first_leg(c):
            if c["dist"] <= WALK_KM:
                return _walk_leg(_safe(p.walk, start, c["stop_ref"], departure), start, c["pos"], departure, "start", c["name"])
            pickup = departure + dt.timedelta(minutes=WAIT_START_MIN)
            offer = _safe(p.vertt_offer, start, c["pos"], pickup)
            return _vertt_leg(offer, pickup, WAIT_START_MIN, "start", c["name"]) if offer else None

        f_first = {c["name"]: pool.submit(first_leg, c) for c in cs}
        f_vo = pool.submit(_safe, p.vertt_offer, start, dest, departure + dt.timedelta(minutes=WAIT_START_MIN))
        f_pt = pool.submit(_safe, p.public_transport_only, start, dest, departure)
        first = {k: f.result() for k, f in f_first.items()}

        # round 2: one train per station pair
        pairs = [(a, b) for a in cs for b in cd if a["stop_ref"] != b["stop_ref"] and first[a["name"]]]
        f_train = {(a["name"], b["name"]): pool.submit(_safe, p.train, a["stop_ref"], b["stop_ref"], first[a["name"]]["arrival"])
                   for a, b in pairs}
        trains = {k: f.result() for k, f in f_train.items()}

        # round 3: prices and last legs
        def last_leg(b, arrive: dt.datetime):
            if b["dist"] <= WALK_KM:
                return _walk_leg(_safe(p.walk, b["stop_ref"], dest, arrive), b["pos"], dest, arrive, b["name"], "destination")
            pickup = arrive + dt.timedelta(minutes=WAIT_DEST_MIN)
            offer = _safe(p.vertt_offer, b["pos"], dest, pickup)
            return _vertt_leg(offer, pickup, WAIT_DEST_MIN, b["name"], "destination") if offer else None

        by_name = {c["name"]: c for c in cd}
        f_price = {k: pool.submit(_safe, p.half_fare_price, t) for k, t in trains.items() if t}
        f_last = {k: pool.submit(last_leg, by_name[k[1]], t["end"]) for k, t in trains.items() if t}
        prices = {k: f.result() for k, f in f_price.items()}
        lasts = {k: f.result() for k, f in f_last.items()}
        vertt_only, pt = f_vo.result(), f_pt.result()

    # price estimate where OJP Fare gave none (PRD-8): CHF/km of the priced trains of this search
    train_km = lambda t: sum(l["km"] for l in t["legs"] if l["kind"] == "train")
    priced = [(prices[k]["price"], train_km(t)) for k, t in trains.items() if t and prices.get(k) and train_km(t)]
    rate = sum(x for x, _ in priced) / sum(k for _, k in priced) if priced else HALF_FARE_CHF_PER_KM
    half = {k: (prices[k]["price"] if prices.get(k) else r05(rate * train_km(t))) for k, t in trains.items() if t}
    for k in half:
        if not prices.get(k):
            print(f"[engine] price estimated {k}: CHF {half[k]:.2f} ({rate:.3f} CHF/km)")   # server log only

    trips = []
    for (a, b), t in trains.items():
        if not t or not lasts.get((a, b)):
            continue
        f, tl, l = first[a], _train_legs(t), lasts[(a, b)]
        legs = [f, *tl, l]
        car_legs = [x for x in (f, l) if x["kind"] == "vertt"]
        trips.append({
            "id": f"{a} → {b}",
            "departure": departure, "arrival": l["arrival"],
            "duration_min": round((l["arrival"] - departure).total_seconds() / 60),
            "transfers": t["transfers"],
            "train_price_half_chf": half[(a, b)],
            "price_chf": {c: r05(sum(x["price_chf"] for x in car_legs) + _train_price(half[(a, b)], c)) for c in TRAVELCARDS},
            "co2_kg": round(sum(x["co2_kg"] for x in legs if "co2_kg" in x), 2),
            "legs": legs})
    if not trips:
        return {**base, "status": "no_trip", "message": "No trip found for this time", "trips": [], "comparisons": _comparisons(vertt_only, pt, departure, rate)}

    # labels per travelcard; only trips that carry a label for at least one travelcard are shown
    for t in trips:
        t["labels"] = {c: [] for c in TRAVELCARDS}
    for c in TRAVELCARDS:
        for label, key in (("Fastest", lambda t: (t["arrival"], t["price_chf"][c])),
                           ("Cheapest", lambda t: (t["price_chf"][c], t["arrival"])),
                           ("Greenest", lambda t: (t["co2_kg"], t["arrival"]))):
            min(trips, key=key)["labels"][c].append(label)
    shown = [t for t in trips if any(t["labels"].values())]
    return _serialise({**base, "status": "ok", "trips": sorted(shown, key=lambda t: t["arrival"]),
                       "comparisons": _comparisons(vertt_only, pt, departure, rate)})


def _comparisons(vertt_only, pt, departure: dt.datetime, rate: float) -> dict:
    out = {"vertt_only": None, "public_transport_only": None}
    if vertt_only:
        pickup = departure + dt.timedelta(minutes=WAIT_START_MIN)
        out["vertt_only"] = {"departure": departure, "arrival": pickup + dt.timedelta(minutes=vertt_only["ride_time_min"]),
                             "distance_km": vertt_only["distance_km"], "price_chf": r05(vertt_only["price_chf"]),
                             "co2_kg": vertt_only["co2_kg"], "car": vertt_only["car"]}
    if pt:
        km = sum(l["km"] for l in pt["legs"] if l["kind"] == "train")
        half = pt["price"]["price"] if pt.get("price") else r05(rate * km)
        out["public_transport_only"] = {"departure": pt["start"], "arrival": pt["end"], "transfers": pt["transfers"],
                                        "price_chf": {c: _train_price(half, c) for c in TRAVELCARDS},
                                        "co2_kg": round(sum(l.get("co2_kg", 0) for l in pt["legs"]), 2)}
    return _serialise(out)


if __name__ == "__main__":                  # quick local try with real data
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    import json
    import time
    for name, s, d in (("Wettswil -> Ostermundigen", (47.3416, 8.4708), (46.9565, 7.4870)),
                       ("Winterthur -> Bern", (47.4993, 8.7290), (46.9468, 7.4442))):
        t0 = time.time()
        r = search(s, d, dt.datetime(2026, 10, 13, 8, 0, tzinfo=ojp.SWISS))
        print(f"\n=== {name}: {r['status']} in {time.time() - t0:.1f} s")
        for t in r["trips"]:
            lines = [l.get("line") or l["kind"] for l in t["legs"] if l["kind"] != "transfer"]
            print(f"  {t['id']:28} {t['departure'][11:]}-{t['arrival'][11:]}  CHF {t['price_chf']['half']:6.2f} (half-fare)"
                  f"  CO2 {t['co2_kg']:.1f} kg  {lines}  labels {t['labels']['half']}")
        print("  comparisons:", json.dumps({k: (v and {kk: v[kk] for kk in ('arrival', 'price_chf', 'co2_kg')}) for k, v in r["comparisons"].items()}, ensure_ascii=False))
