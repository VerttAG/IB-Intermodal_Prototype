"""Tests for the trip engine (PRD-8) with fake partners – no internet.  Run: pytest"""
import datetime as dt
import json

import httpx
import pytest

from src import engine, vertt
from src.ojp import SWISS

WETTSWIL, OSTERMUNDIGEN = (47.3416, 8.4708), (46.9565, 7.4870)
WINTERTHUR_ADDR, BERN_ADDR = (47.4993, 8.7290), (46.9468, 7.4442)
AT = dt.datetime(2026, 10, 13, 8, 0, tzinfo=SWISS)
CAR = {"make": "VW", "model": "Passat", "year": 2013, "co2_g_per_km": 123}


def names(cands):
    return [c["name"] for c in cands]


@pytest.mark.parametrize("start, dest, start_hubs, dest_hubs", [      # reference cases PRD-8 AC-11
    (WETTSWIL, OSTERMUNDIGEN, ["Zürich HB", "Hedingen"], ["Bern"]),
    ((47.3470, 8.7180), (46.9468, 7.4442), ["Zürich HB", "Wetzikon ZH"], ["Bern"]),
    ((47.0850, 8.4420), (46.1930, 9.0210), ["Luzern", "Arth-Goldau"], ["Lugano", "Bellinzona"]),
])
def test_tier_rule(start, dest, start_hubs, dest_hubs):
    assert names(engine.candidates(start, start, dest)) == start_hubs
    assert names(engine.candidates(dest, start, dest)) == dest_hubs


class Fake:
    """Fake partners: Vertt km = 1.3 × straight line; trains as configured per start station."""
    def __init__(self, trains, prices, no_vertt_to=None):
        self.trains, self.prices, self.no_vertt_to, self.train_calls = trains, prices, no_vertt_to, []

    def vertt_offer(self, a, b, pickup):
        if self.no_vertt_to and tuple(b) == self.no_vertt_to:
            return None
        km = vertt.straight_km(a, b) * 1.3
        minutes = km * 1.6
        return {"offer_id": "x", "distance_km": round(km, 3), "ride_time_min": round(minutes, 1), "price_chf": vertt.tariff(km, minutes),
                "car": CAR, "co2_kg": round(km * 0.123, 3), "route": [list(a), list(b)]}

    def walk(self, a, b, when):
        return {"minutes": 6.0, "km": 0.5, "route": [[0, 0], [0, 0]]}

    def train(self, frm, to, arrival):
        self.train_calls.append((frm, to))
        if frm not in self.trains:
            return None
        dep_after, minutes, km = self.trains[frm]
        dep = arrival + dt.timedelta(minutes=8 + dep_after)
        arr = dep + dt.timedelta(minutes=minutes)
        return {"start": dep, "end": arr, "transfers": 0, "xml": frm,
                "legs": [{"kind": "train", "line": "IC", "from": frm, "to": to, "dep": dep, "arr": arr, "platform": "1",
                          "km": km, "co2_kg": round(km * 0.007, 3), "route": []}]}

    def half_fare_price(self, trip):
        price = self.prices.get(trip["xml"])
        return {"product": "Streckenbillett", "price": price} if price else None

    def public_transport_only(self, a, b, when):
        return {"start": when, "end": when + dt.timedelta(minutes=140), "transfers": 2, "price": {"price": 31.0},
                "legs": [{"kind": "train", "km": 120, "co2_kg": 0.84}]}

    def partners(self):
        return engine.Partners(self.vertt_offer, self.walk, self.train, self.half_fare_price, self.public_transport_only)


ZHB, HEDINGEN = "ch:1:sloid:3000", "ch:1:sloid:2223"


def run(fake, start=WETTSWIL, dest=OSTERMUNDIGEN):
    return engine.search(start, dest, AT, now=AT, partners=fake.partners())


def test_labels_prices_and_travelcards():
    # Zürich HB: faster train; Hedingen: slower train but shorter Vertt ride
    fake = Fake(trains={ZHB: (5, 57, 118), HEDINGEN: (0, 100, 125)}, prices={ZHB: 26.5, HEDINGEN: 27.0})
    r = run(fake)
    assert r["status"] == "ok"
    trips = {t["id"]: t for t in r["trips"]}
    zhb, hed = trips["Zürich HB → Bern"], trips["Hedingen → Bern"]
    assert zhb["labels"]["half"] == ["Fastest"] and hed["labels"]["half"] == ["Cheapest", "Greenest"]
    for t in (zhb, hed):
        cars = sum(l["price_chf"] for l in t["legs"] if l["kind"] == "vertt")
        assert t["price_chf"]["half"] == engine.r05(cars + t["train_price_half_chf"])
        assert t["price_chf"]["none"] == engine.r05(cars + 2 * t["train_price_half_chf"])
        assert t["price_chf"]["ga"] == engine.r05(cars)
    first = zhb["legs"][0]
    assert first["kind"] == "vertt" and first["pickup"] == "2026-10-13T08:05+02:00" and first["car"] == CAR
    last = zhb["legs"][-1]
    assert last["kind"] == "vertt" and last["wait_min"] == 2
    json.dumps(r)                                              # the answer is plain JSON


def test_price_estimate_when_ojp_fare_gives_none():
    fake = Fake(trains={ZHB: (5, 57, 118), HEDINGEN: (0, 100, 125)}, prices={ZHB: 26.5})      # Hedingen: no price
    hed = {t["id"]: t for t in run(fake)["trips"]}["Hedingen → Bern"]
    assert hed["train_price_half_chf"] == engine.r05(26.5 / 118 * 125)


def test_walk_at_both_ends_gives_a_train_only_trip():
    fake = Fake(trains={"ch:1:sloid:6000": (0, 87, 140)}, prices={"ch:1:sloid:6000": 30.5})
    r = run(fake, WINTERTHUR_ADDR, BERN_ADDR)
    t = r["trips"][0]
    assert [l["kind"] for l in t["legs"]] == ["walk", "train", "walk"]
    assert t["price_chf"] == {"none": 61.0, "half": 30.5, "ga": 0.0}
    assert t["labels"]["half"] == ["Fastest", "Cheapest", "Greenest"]


def test_trip_dropped_if_last_vertt_leg_not_served():
    fake = Fake(trains={ZHB: (5, 57, 118)}, prices={ZHB: 26.5}, no_vertt_to=OSTERMUNDIGEN)
    r = run(fake)
    assert r["status"] == "no_trip" and r["trips"] == []


def test_never_asks_for_a_train_from_a_station_to_itself():
    fake = Fake(trains={}, prices={})
    engine.search((46.2500, 7.3450), (46.5197, 6.6323), AT, now=AT, partners=fake.partners())   # Sion -> Lausanne
    assert all(frm != to for frm, to in fake.train_calls)


def test_short_trip_and_past_time():
    fake = Fake(trains={}, prices={})
    assert run(fake, WETTSWIL, (47.37818, 8.54021))["status"] == "not_suitable"              # Wettswil -> Zürich HB, ~6 km
    with pytest.raises(engine.SearchError, match="future"):
        engine.search(WETTSWIL, OSTERMUNDIGEN, AT, now=AT + dt.timedelta(minutes=6), partners=fake.partners())
    assert run(fake)["status"] == "no_trip"                                                   # 5 min tolerance not hit


def test_rate_limit_stops_the_search():
    fake = Fake(trains={ZHB: (5, 57, 118)}, prices={})

    def limited(*args):
        raise httpx.HTTPStatusError("429", request=httpx.Request("POST", "x"), response=httpx.Response(429))
    fake.train = limited
    with pytest.raises(engine.SearchError, match="Too many"):
        run(fake)
