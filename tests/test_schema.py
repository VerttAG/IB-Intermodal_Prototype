"""docs/schema.md stays true: its full example is exactly what the code produces (PRD-5 AC-17).  Run: pytest"""
import json
import random
import re
from pathlib import Path

from src import settlement

TRIP = {"train_price_half_chf": 8.40, "legs": [{"kind": "vertt", "distance_km": 10, "ride_time_min": 30, "co2_kg": 1.2},
                                               {"kind": "train", "co2_kg": 0.088}]}


def test_schema_example_matches_the_code():
    doc = (Path(__file__).parents[1] / "docs" / "schema.md").read_text(encoding="utf-8")
    example = json.loads(re.findall(r"```json\n(.*?)```", doc, re.S)[0])
    rec = settlement.book(TRIP, "vertt", "half", 0, "twint", "swisspass", now="2026-10-19T08:12:05+02:00", rng=random.Random(1))
    rec = settlement.cancel(rec, now="2026-10-19T08:20:41+02:00")
    rec["booking"]["customer"] = example["booking"]["customer"]        # random by design
    assert example == rec
    assert example["schema_version"] == settlement.SCHEMA_VERSION
