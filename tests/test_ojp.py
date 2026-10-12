"""Tests for the OJP client (PRD-6, PRD-8) on saved real OJP answers – no internet.  Run: pytest"""
import datetime as dt
from pathlib import Path

import pytest

from src import ojp

FIX = Path(__file__).parent / "fixtures" / "ojp"
ZURICH_HB, BERN, WINTERTHUR = "ch:1:sloid:3000", "ch:1:sloid:7000", "ch:1:sloid:6000"
at = lambda h, m: dt.datetime(2026, 10, 13, h, m, tzinfo=ojp.SWISS)


@pytest.fixture(autouse=True)
def fresh_cache():
    ojp._cache.clear()


@pytest.fixture
def answers(monkeypatch):
    """Replace the network: every call returns the given saved answer and is recorded."""
    calls = []

    def use(*files):
        queue = list(files)

        def fake_post(url, xml, key_name):
            calls.append((url, xml))
            return (FIX / (queue.pop(0) if len(queue) > 1 else queue[0])).read_bytes()
        monkeypatch.setattr(ojp, "_post", fake_post)
        return calls
    return use


def trains(trip):
    return [l["line"] for l in trip["legs"] if l["kind"] == "train"]


def test_times_and_durations():
    assert ojp.minutes("PT1H5M30S") == 65.5
    assert ojp.local("2026-10-13T07:01:00Z").strftime("%H:%M %z") == "09:01 +0200"   # summer time
    assert ojp.local("2026-10-27T07:00:00Z").strftime("%H:%M %z") == "08:00 +0100"   # winter time


def test_parse_trips():
    trips = ojp.parse_trips((FIX / "trip_zurich_bern.xml").read_bytes())
    assert [trains(t) for t in trips] == [["RE37", "S26", "IC6"], ["IR35"], ["IC81"], ["IR16"], ["IR37", "IR16"]]
    ic = trips[2]["legs"][0]
    assert (f"{ic['dep']:%H:%M}", f"{ic['arr']:%H:%M}", ic["platform"]) == ("09:01", "09:58", "31")
    assert ic["km"] == pytest.approx(118.2, abs=0.5)
    assert ic["co2_kg"] == pytest.approx(ic["km"] * 0.007, abs=0.001)
    assert len(ic["route"]) >= 2


def test_rule_prefers_fewer_transfers_within_10_min():
    trips = ojp.parse_trips((FIX / "trip_zurich_bern.xml").read_bytes())
    # RE37+S26+IC6 arrives 09:56 with 2 transfers, IC81 09:58 direct -> IC81
    assert trains(ojp.choose_train(trips, at(8, 38))) == ["IC81"]
    assert trains(ojp.choose_train(trips, at(8, 54))) == ["IC81"]      # RE37 and IR35 already gone
    assert ojp.choose_train(trips, at(9, 10)) is None                  # nothing leaves late enough


def test_trains_only():
    trips = ojp.parse_trips((FIX / "trip_with_bus.xml").read_bytes())
    assert any(l["kind"] == "other_pt" for l in trips[0]["legs"])     # this connection uses a bus
    assert ojp.choose_train(trips, at(8, 0)) is None


def test_train_asks_for_arrival_plus_8_min(answers):
    calls = answers("trip_zurich_bern.xml")
    t = ojp.train(ZURICH_HB, BERN, at(8, 30))
    assert trains(t) == ["IC81"]
    assert "<DepArrTime>2026-10-13T06:38:00Z</DepArrTime>" in calls[0][1]   # 08:38 Swiss time
    ojp.train(ZURICH_HB, BERN, at(8, 30))
    assert len(calls) == 1                                                  # second time from the cache


def test_walk(answers):
    answers("trip_walk_winterthur.xml")
    w = ojp.walk((47.4993, 8.7290), WINTERTHUR, at(8, 0))
    assert w["minutes"] == pytest.approx(8.2, abs=0.5) and w["km"] == pytest.approx(0.54, abs=0.05)


def test_half_fare_price(answers):
    answers("fare_ok.xml")
    trip = ojp.choose_train(ojp.parse_trips((FIX / "trip_zurich_bern.xml").read_bytes()), at(8, 38))
    assert ojp.half_fare_price(trip) == {"product": "Streckenbillett", "price": 26.5}


def test_no_price_from_nova_after_one_retry(answers):
    calls = answers("fare_nova_error.xml")
    trip = ojp.parse_trips((FIX / "trip_zurich_bern.xml").read_bytes())[0]
    assert ojp.half_fare_price(trip) is None
    assert len(calls) == 2                                                  # asked twice


def test_fare_request_sends_the_trip_without_geometry():
    trip = ojp.parse_trips((FIX / "trip_zurich_bern.xml").read_bytes())[2]
    req = ojp._fare_request(trip["xml"])
    assert "<EntitlementProductRef>HTA</EntitlementProductRef>" in req and "LinkProjection" not in req


def test_parse_fare_garbage():
    assert ojp.parse_fare(b"not xml") is None
