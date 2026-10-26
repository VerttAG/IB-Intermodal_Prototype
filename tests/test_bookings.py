"""Tests for the booking entrance and the store, local and online (PRD-5, issue #22).  Run: pytest"""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("bookings_api", Path(__file__).parents[1] / "api" / "bookings.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

TRIP = {"train_price_half_chf": 8.40, "legs": [
    {"kind": "vertt", "distance_km": 10, "ride_time_min": 30, "co2_kg": 1.0},
    {"kind": "train", "co2_kg": 0.5}]}


@pytest.fixture(autouse=True)
def temp_store(tmp_path, monkeypatch):
    monkeypatch.setenv("BOOKING_STORE_DIR", str(tmp_path))
    for name in ("KV_REST_API_URL", "KV_REST_API_TOKEN", "UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def book():
    return api.handle_post({"action": "book", "trip": TRIP, "system": "vertt", "travelcard": "half", "promo_percent": 0,
                            "payment_method": "visa", "login_method": "email"})


def test_book_then_read_the_data_link():
    status, rec = book()
    assert status == 200 and rec["booking"]["total_chf"] == 38.40
    status, again = api.handle_get({"id": [rec["booking"]["booking_id"]]})
    assert status == 200 and again == rec


def test_cancel_updates_the_same_link():
    _, rec = book()
    bid = rec["booking"]["booking_id"]
    status, done = api.handle_post({"action": "cancel", "booking_id": bid})
    assert status == 200 and done["booking"]["status"] == "cancelled"
    assert api.handle_get({"id": [bid]})[1]["booking"]["status"] == "cancelled"
    assert api.handle_post({"action": "cancel", "booking_id": bid})[0] == 409


def test_unknown_and_bad_requests():
    assert api.handle_get({"id": ["BK-000000"]})[0] == 404
    assert api.handle_get({"id": ["../../.env"]})[0] == 404          # never a path from outside
    assert api.handle_post({"action": "pay"})[0] == 400
    assert api.handle_post({"action": "book", "trip": TRIP, "system": "vertt"})[0] == 400


def test_online_store_when_upstash_is_connected(monkeypatch, tmp_path):
    from src import store
    redis, calls = {}, []

    class Answer:
        def __init__(self, result): self.result = result
        def raise_for_status(self): pass
        def json(self): return {"result": self.result}

    def fake_post(url, json, headers, timeout):          # stands in for Upstash's REST interface
        calls.append((url, headers["Authorization"]))
        command, key, *value = json
        if command == "SET":
            redis[key] = value[0]
            return Answer("OK")
        return Answer(redis.get(key))

    monkeypatch.setenv("KV_REST_API_URL", "https://example.upstash.io")
    monkeypatch.setenv("KV_REST_API_TOKEN", "test-token")
    monkeypatch.setattr(store.httpx, "post", fake_post)
    _, rec = book()
    bid = rec["booking"]["booking_id"]
    assert f"booking:{bid}" in redis and not list(tmp_path.iterdir())   # online, not in the local folder
    assert api.handle_get({"id": [bid]}) == (200, rec)
    assert api.handle_get({"id": ["BK-000000"]})[0] == 404
    assert calls[0] == ("https://example.upstash.io", "Bearer test-token")


def test_booking_numbers_stay_unique(monkeypatch):
    first = book()[1]
    real_book, drawn = api.settlement.book, []

    def book_twice(*args):                                 # the first draw repeats an existing number
        rec = real_book(*args)
        if not drawn:
            rec["booking"]["booking_id"] = first["booking"]["booking_id"]
        drawn.append(rec["booking"]["booking_id"])
        return rec

    monkeypatch.setattr(api.settlement, "book", book_twice)
    status, second = book()
    assert status == 200 and len(drawn) == 2 and second["booking"]["booking_id"] != first["booking"]["booking_id"]
    assert api.handle_get({"id": [first["booking"]["booking_id"]]})[1] == first          # the first booking is untouched
