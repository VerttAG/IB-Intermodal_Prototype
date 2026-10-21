"""Settlement – who pays whom for a booking, and what a cancellation adds (PRD-4, data format PRD-5).

book(trip, system, travelcard, promo_percent, payment_method, login_method) -> booking record
cancel(record) -> the same record with refund and reversals added (nothing changed or removed)

The record is exactly the content of the data link: booking, amount and CO₂ per leg, settlement events.
Money is calculated with Decimal (exact cents), customer amounts rounded to CHF 0.05.
"""
from __future__ import annotations

import copy
import datetime as dt
import random
import secrets
from decimal import ROUND_HALF_UP, Decimal

from src import vertt
from src.ojp import SWISS

SCHEMA_VERSION = "2"                       # docs/schema.md – raise it when a field name or meaning changes
COMMISSION_RATE = Decimal("0.05")          # Vertt app only: 5 % of the train ticket, paid by SBB to Vertt
SELLER = {"vertt": "Vertt", "sbb": "SBB"}
TRAVELCARDS = ("none", "half", "ga")
PROMOS = (0, 5, 10, 20)
PAYMENT_METHODS = ("card", "twint", "invoice", "business")
LOGIN_METHODS = ("google", "apple", "swisspass", "email")


class AlreadyCancelled(Exception):
    pass


def money(x) -> Decimal:
    return Decimal(str(x))


def r05(x: Decimal) -> Decimal:
    """Round to CHF 0.05 (customer amounts)."""
    return ((x * 20).quantize(Decimal("1"), ROUND_HALF_UP) / 20).quantize(Decimal("0.01"))


def cents(x: Decimal) -> Decimal:
    """Exact to the centime, half up (B2B amounts)."""
    return x.quantize(Decimal("0.01"), ROUND_HALF_UP)


def _now() -> str:
    return dt.datetime.now(SWISS).isoformat(timespec="seconds")


def book(trip: dict, system: str, travelcard: str, promo_percent: int, payment_method: str, login_method: str,
         now: str | None = None, rng: random.Random | None = None) -> dict:
    """The booking record for a trip of the trip engine (docs/api/trip-offers.md). Raises ValueError for bad input."""
    for value, allowed, name in ((system, SELLER, "system"), (travelcard, TRAVELCARDS, "travelcard"), (promo_percent, PROMOS, "promo_percent"),
                                 (payment_method, PAYMENT_METHODS, "payment_method"), (login_method, LOGIN_METHODS, "login_method")):
        if value not in allowed:
            raise ValueError(f"{name} must be one of {list(allowed)}")
    rng = rng or random.Random()
    booked_at = now or _now()
    booking_id = f"BK-{rng.randrange(100000, 1000000)}"

    # amounts per leg – recalculated here, not taken from the browser (PRD-4, decided 2026-10-12)
    legs, promo_chf, train_co2, has_train = [], Decimal("0"), 0.0, False
    for leg in trip["legs"]:
        if leg["kind"] == "vertt":
            base = r05(money(vertt.tariff(leg["distance_km"], leg["ride_time_min"])))
            paid = r05(base * (1 - Decimal(promo_percent) / 100))          # promo per Vertt ride (decided 2026-10-12)
            promo_chf += base - paid
            legs.append({"operator": "Vertt", "type": "vertt_ride", "amount_before_promo_chf": base, "amount_chf": paid,
                         "co2_kg": round(leg["co2_kg"], 3)})
        elif leg["kind"] == "train":
            has_train, train_co2 = True, train_co2 + leg["co2_kg"]
    if has_train:                                                            # one SBB ticket for all train legs
        half = money(trip["train_price_half_chf"])
        train = {"none": r05(2 * half), "half": r05(half), "ga": Decimal("0.00")}[travelcard]
        first_train = next(i for i, l in enumerate(trip["legs"]) if l["kind"] == "train")
        position = sum(1 for l in trip["legs"][:first_train] if l["kind"] == "vertt")
        legs.insert(position, {"operator": "SBB", "type": "train", "amount_chf": train, "co2_kg": round(train_co2, 3)})
    for i, leg in enumerate(legs, 1):
        leg["seq"] = i

    total = sum((l["amount_chf"] for l in legs), Decimal("0"))
    record = {
        "schema_version": SCHEMA_VERSION,
        "summary": {},                                                     # filled by _summary() – first thing a partner reads
        "booking": {"booking_id": booking_id, "system": system, "status": "paid", "customer": f"demo-{secrets.token_hex(2)}",
                    "login_method": login_method, "travelcard": travelcard, "promo_percent": promo_percent,
                    "promo_chf": promo_chf, "payment_method": payment_method, "booked_at": booked_at, "total_chf": total},
        "legs": legs,
        "settlement_events": [],
    }
    seller = SELLER[system]
    vertt_part = sum((l["amount_chf"] for l in legs if l["operator"] == "Vertt"), Decimal("0"))
    train_part = sum((l["amount_chf"] for l in legs if l["operator"] == "SBB"), Decimal("0"))
    _add(record, booked_at, "b2c_payment", "customer", seller, total, "Customer pays the seller for the whole journey")
    if system == "vertt" and train_part > 0:
        _add(record, booked_at, "b2b_transfer", "Vertt", "SBB", train_part, "Train ticket sold by Vertt")
        _add(record, booked_at, "commission", "SBB", "Vertt", cents(train_part * COMMISSION_RATE), "5 % sales commission on the train ticket")
    elif system == "sbb" and vertt_part > 0:
        _add(record, booked_at, "b2b_transfer", "SBB", "Vertt", vertt_part, "Vertt rides sold by SBB, no commission")
    return _plain(_summary(record))


def cancel(record: dict, now: str | None = None) -> dict:
    """Cancel the whole journey: refund + one reversal per B2B event. Only adds events (PRD-4 US-4)."""
    if record["booking"]["status"] == "cancelled":
        raise AlreadyCancelled(record["booking"]["booking_id"])
    out = copy.deepcopy(record)
    at = now or _now()
    seller = SELLER[out["booking"]["system"]]
    before = list(out["settlement_events"])
    payment = next(e for e in before if e["event_type"] == "b2c_payment")
    _add(out, at, "refund", seller, "customer", money(payment["amount_chf"]), "Journey cancelled, full refund", payment["event_id"])
    for e in before:
        if e["event_type"] in ("b2b_transfer", "commission"):
            _add(out, at, "reversal", e["payee"], e["payer"], money(e["amount_chf"]), f"Reversal of {e['event_type']}", e["event_id"])
    out["booking"]["status"] = "cancelled"
    return _plain(_summary(out))


def balances(record: dict) -> dict:
    """What each party ends with for this booking (customer negative = paid)."""
    out = {"customer": Decimal("0"), "Vertt": Decimal("0"), "SBB": Decimal("0")}
    for e in record["settlement_events"]:
        out[e["payer"]] -= money(e["amount_chf"])
        out[e["payee"]] += money(e["amount_chf"])
    return out


def _summary(record: dict) -> dict:
    """CO₂ per operator and the net transfer between Vertt and SBB over all events (0 after a cancellation)."""
    co2 = lambda op: round(sum(l["co2_kg"] for l in record["legs"] if op in (None, l["operator"])), 3)
    vertt_to_sbb = sum((money(e["amount_chf"]) * (1 if e["payer"] == "Vertt" else -1) for e in record["settlement_events"]
                        if {e["payer"], e["payee"]} == {"Vertt", "SBB"}), Decimal("0"))
    payer, payee = ("Vertt", "SBB") if vertt_to_sbb > 0 else ("SBB", "Vertt") if vertt_to_sbb < 0 else (None, None)
    record["summary"] = {"co2_kg": {"vertt": co2("Vertt"), "sbb": co2("SBB"), "total": co2(None)},
                         "settlement": {"payer": payer, "payee": payee, "amount_chf": abs(vertt_to_sbb)}}
    return record


def _add(record, at, event_type, payer, payee, amount, reason, refers_to=None):
    events = record["settlement_events"]
    booking_id = record["booking"]["booking_id"]
    events.append({"event_id": f"{booking_id}-ev{len(events) + 1}", "booking_id": booking_id, "seq": len(events) + 1,
                   "timestamp": at, "event_type": event_type, "payer": payer, "payee": payee,
                   "amount_chf": amount, "reason": reason, "refers_to_event": refers_to})


def _plain(x):
    """Decimal -> float with two decimals, for JSON."""
    if isinstance(x, Decimal):
        return float(x.quantize(Decimal("0.01")))
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_plain(v) for v in x]
    return x
