"""Tests for the Vertt API (PRD-7). Valhalla is faked – the tests run without internet.  Run: pytest"""
from datetime import datetime

import pytest

from src import vertt

WETTSWIL, ZURICH_HB, MILANO = (47.3416, 8.4708), (47.37818, 8.54021), (45.4642, 9.1900)
PICKUP = datetime.fromisoformat("2026-10-13T08:05+02:00")


def fake_route(a, b):
    return 13.506, 22.1, [a, (47.36, 8.50), b]


def no_route(a, b):
    raise vertt.NotServed("no_route")


@pytest.mark.parametrize("km, minutes, price", [
    (10, 5, 22.50),          # reference cases from PRD-7 (3 + 18 + 1.50)
    (2, 3, 10.00),           # 7.50 raised to the minimum price
    (13.172, 21.2, 33.07),   # a recorded ride
])
def test_tariff(km, minutes, price):
    assert vertt.tariff(km, minutes) == price


def test_offer_fields_and_price():
    o = vertt.calculate_offer(WETTSWIL, ZURICH_HB, PICKUP, fake_route)
    assert o["status"] == "offer" and o["version"] == "1"
    assert o["price_chf"] == vertt.tariff(13.506, 22.1)
    assert o["co2_kg"] == round(13.506 * o["car"]["co2_g_per_km"] / 1000, 3)
    assert o["car"] in [{k: c[k] for k in ("make", "model", "year", "co2_g_per_km")} for c in vertt.car_pool()]
    assert len(o["route"]) == 3


def test_same_request_same_offer_and_car():
    a = vertt.calculate_offer(WETTSWIL, ZURICH_HB, PICKUP, fake_route)
    b = vertt.calculate_offer(WETTSWIL, ZURICH_HB, PICKUP, fake_route)
    assert a == b


def test_price_does_not_depend_on_car():
    prices = {vertt.calculate_offer(WETTSWIL, ZURICH_HB, PICKUP.replace(minute=m), fake_route)["price_chf"] for m in range(20)}
    assert len(prices) == 1


@pytest.mark.parametrize("start, dest, reason, route", [
    (WETTSWIL, (47.3420, 8.4710), "too_short", fake_route),
    (MILANO, ZURICH_HB, "outside_switzerland", fake_route),
    (WETTSWIL, ZURICH_HB, "no_route", no_route),
])
def test_not_served(start, dest, reason, route):
    with pytest.raises(vertt.NotServed, match=reason):
        vertt.calculate_offer(start, dest, PICKUP, route)


def test_request_needs_the_secret():
    body = {"start": {"lat": WETTSWIL[0], "lon": WETTSWIL[1]}, "destination": {"lat": ZURICH_HB[0], "lon": ZURICH_HB[1]},
            "pickup_time": "2026-10-13T08:05+02:00"}
    assert vertt.handle_request(body, None, "s3cret", fake_route)[0] == 403
    assert vertt.handle_request(body, "wrong", "s3cret", fake_route)[0] == 403
    assert vertt.handle_request(body, "s3cret", None, fake_route)[0] == 403      # not configured -> nobody gets in
    status, answer = vertt.handle_request(body, "s3cret", "s3cret", fake_route)
    assert status == 200 and answer["status"] == "offer"


def test_invalid_request_and_not_served_answers():
    assert vertt.handle_request({"start": "x"}, "s", "s", fake_route)[0] == 400
    body = {"start": {"lat": 45.46, "lon": 9.19}, "destination": {"lat": 47.37, "lon": 8.54}, "pickup_time": "2026-10-13T08:05+02:00"}
    status, answer = vertt.handle_request(body, "s", "s", fake_route)
    assert status == 200 and answer == {"version": "1", "status": "not_served", "reason": "outside_switzerland"}
