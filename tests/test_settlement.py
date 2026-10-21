"""Tests for the settlement (PRD-4) and the data link content (PRD-5).  Run: pytest"""
import json
import random
from decimal import Decimal

import pytest

from src import settlement as st


def vertt_leg(km, minutes, co2=1.0):
    return {"kind": "vertt", "distance_km": km, "ride_time_min": minutes, "co2_kg": co2, "price_chf": 999,   # 999 = tampered, ignored
            "route": [[47.3, 8.4]], "car": {"make": "VW"}}


def train_leg(co2=0.5):
    return {"kind": "train", "line": "IC", "co2_kg": co2, "route": []}


def trip(half, *legs):
    return {"train_price_half_chf": half, "legs": list(legs)}


REF = trip(8.40, vertt_leg(10, 30), train_leg())          # tariff 3 + 18 + 9 = CHF 30.00, train half-fare CHF 8.40


def book(t=REF, system="vertt", card="half", promo=0):
    return st.book(t, system, card, promo, "twint", "google", now="2026-10-13T07:50:00+02:00", rng=random.Random(1))


def events(rec):
    return [(e["event_type"], e["payer"], e["payee"], e["amount_chf"]) for e in rec["settlement_events"]]


def test_reference_case_vertt_app():                       # PRD-4 AC-15
    rec = book()
    assert events(rec) == [("b2c_payment", "customer", "Vertt", 38.40), ("b2b_transfer", "Vertt", "SBB", 8.40),
                           ("commission", "SBB", "Vertt", 0.42)]
    b = st.balances(rec)
    assert (b["Vertt"], b["SBB"], b["customer"]) == (Decimal("30.42"), Decimal("7.98"), Decimal("-38.40"))


def test_reference_case_sbb_app():
    rec = book(system="sbb")
    assert events(rec) == [("b2c_payment", "customer", "SBB", 38.40), ("b2b_transfer", "SBB", "Vertt", 30.00)]
    b = st.balances(rec)
    assert (b["Vertt"], b["SBB"]) == (Decimal("30.00"), Decimal("8.40"))


@pytest.mark.parametrize("card, train, transfer", [("none", 16.80, True), ("half", 8.40, True), ("ga", 0.0, False)])
def test_travelcards(card, train, transfer):
    rec = book(card=card)
    assert [l["amount_chf"] for l in rec["legs"]] == [30.00, train]
    types = [e["event_type"] for e in rec["settlement_events"]]
    assert ("b2b_transfer" in types) == transfer and ("commission" in types) == transfer
    sbb = book(card=card, system="sbb")                    # SBB app passes the Vertt part on, also with GA
    assert ("b2b_transfer", "SBB", "Vertt", 30.00) in events(sbb)


def test_promo_only_on_vertt_and_carried_by_vertt():       # AC-6, AC-8
    rec = book(promo=10)
    assert rec["legs"][0]["amount_chf"] == 27.00 and rec["booking"]["promo_chf"] == 3.00
    assert rec["legs"][0]["amount_before_promo_chf"] == 30.00 and "amount_before_promo_chf" not in rec["legs"][1]
    assert events(rec)[1:] == [("b2b_transfer", "Vertt", "SBB", 8.40), ("commission", "SBB", "Vertt", 0.42)]
    assert ("b2b_transfer", "SBB", "Vertt", 27.00) in events(book(promo=10, system="sbb"))


def test_promo_per_vertt_ride_rounded_to_005():
    two = trip(8.40, vertt_leg(4.1, 13), train_leg(), vertt_leg(3.5, 8))   # 14.28 -> 14.30 and 11.70
    rec = book(two, promo=10)
    assert [l["amount_chf"] for l in rec["legs"]] == [12.85, 8.40, 10.55]    # 12.87 -> 12.85, 10.53 -> 10.55
    assert [l["type"] for l in rec["legs"]] == ["vertt_ride", "train", "vertt_ride"]


@pytest.mark.parametrize("half, commission", [(8.50, 0.43), (8.45, 0.42), (26.50, 1.33)])   # 0.425 / 0.4225 / 1.325 half up
def test_commission_rounded_half_up(half, commission):
    assert events(book(trip(half, vertt_leg(10, 30), train_leg())))[2][3] == commission


def test_amounts_are_recalculated_and_trains_combined():
    t = trip(31.40, vertt_leg(6.7, 12.4, 0.8), train_leg(0.07), {"kind": "transfer", "minutes": 4}, train_leg(0.83),
             {"kind": "walk", "minutes": 6, "co2_kg": 0.0})
    rec = book(t)
    assert [(l["seq"], l["operator"], l["amount_chf"]) for l in rec["legs"]] == [(1, "Vertt", 18.80), (2, "SBB", 31.40)]
    assert rec["legs"][1]["co2_kg"] == 0.9 and rec["summary"]["co2_kg"] == {"vertt": 0.8, "sbb": 0.9, "total": 1.7}


def test_everything_adds_up():                             # AC-14
    for system in ("vertt", "sbb"):
        for card in st.TRAVELCARDS:
            rec = book(system=system, card=card, promo=20)
            b = st.balances(rec)
            assert b["Vertt"] + b["SBB"] == -b["customer"] == Decimal(str(rec["booking"]["total_chf"]))


def test_cancel():
    rec = book()
    done = st.cancel(rec, now="2026-10-13T07:55:00+02:00")
    assert done["booking"]["status"] == "cancelled" and rec["booking"]["status"] == "paid"
    assert done["settlement_events"][:3] == rec["settlement_events"]                  # AC-23: unchanged
    assert events(done)[3:] == [("refund", "Vertt", "customer", 38.40), ("reversal", "SBB", "Vertt", 8.40),
                                ("reversal", "Vertt", "SBB", 0.42)]
    assert [e["refers_to_event"] for e in done["settlement_events"][3:]] == [e["event_id"] for e in rec["settlement_events"]]
    assert all(v == 0 for v in st.balances(done).values())                           # AC-24
    with pytest.raises(st.AlreadyCancelled):
        st.cancel(done)


def test_data_link_holds_transactional_data_only():        # PRD-5 AC-4 to AC-6
    rec = book()
    assert list(rec) == ["schema_version", "summary", "booking", "legs", "settlement_events"] and rec["schema_version"] == "2"
    assert set(rec["booking"]) == {"booking_id", "system", "status", "customer", "login_method", "travelcard", "promo_percent",
                                   "promo_chf", "payment_method", "booked_at", "total_chf"}
    assert set(rec["legs"][0]) == {"seq", "operator", "type", "amount_before_promo_chf", "amount_chf", "co2_kg"}     # Vertt ride
    assert set(rec["legs"][1]) == {"seq", "operator", "type", "amount_chf", "co2_kg"}                                # train
    assert set(rec["settlement_events"][0]) == {"event_id", "booking_id", "seq", "timestamp", "event_type", "payer", "payee",
                                                "amount_chf", "reason", "refers_to_event"}
    text = json.dumps(rec)
    assert not any(f'"{k}":' in text for k in ("route", "car", "lat", "lon", "from", "to", "line"))   # no trip details


def test_bad_input():
    with pytest.raises(ValueError, match="promo_percent"):
        st.book(REF, "vertt", "half", 15, "twint", "google")
    with pytest.raises(ValueError, match="system"):
        st.book(REF, "bls", "half", 0, "twint", "google")


def test_summary_shows_the_net_transfer():                 # schema v2: first lines of the data link
    rec = book()                                           # Vertt app, half-fare: Vertt -> SBB 8.40, SBB -> Vertt 0.42
    assert rec["summary"]["settlement"] == {"payer": "Vertt", "payee": "SBB", "amount_chf": 7.98}
    assert book(system="sbb")["summary"]["settlement"] == {"payer": "SBB", "payee": "Vertt", "amount_chf": 30.00}
    assert book(card="ga")["summary"]["settlement"] == {"payer": None, "payee": None, "amount_chf": 0.00}    # GA: no transfer
    assert st.cancel(rec)["summary"]["settlement"] == {"payer": None, "payee": None, "amount_chf": 0.00}     # all reversed
