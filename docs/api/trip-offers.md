# Trip offers – the answer of the trip engine

Version **1**. Spec: PRD-8. Code: `src/engine.py` (logic), `api/trips.py` (Vercel function). For the booking app.

## Request

`POST /api/trips` – called from the browser, behind the password gate.

```json
{
  "start":       {"lat": 47.3416, "lon": 8.4708},
  "destination": {"lat": 46.9565, "lon": 7.4870},
  "departure":   "2026-10-13T08:00+02:00"
}
```

Coordinates come from the swisstopo address search in the browser (`docs/api/geocoding.md`); `departure` is "depart at", with time zone.

## Answer

```json
{
  "version": "1",
  "status": "ok",
  "departure": "2026-10-13T08:00+02:00",
  "trips": [
    {
      "id": "Hedingen → Bern",
      "departure": "2026-10-13T08:00+02:00",
      "arrival": "2026-10-13T10:13+02:00",
      "duration_min": 133,
      "transfers": 1,
      "train_price_half_chf": 31.4,
      "price_chf": {"none": 100.65, "half": 69.25, "ga": 37.85},
      "co2_kg": 2.8,
      "labels": {"none": ["Fastest", "Cheapest", "Greenest"], "half": ["Fastest", "Cheapest", "Greenest"], "ga": ["Fastest", "Cheapest", "Greenest"]},
      "legs": [
        {"kind": "vertt", "from": "start", "to": "Hedingen", "wait_min": 5, "pickup": "2026-10-13T08:05+02:00", "arrival": "…",
         "ride_time_min": 12.4, "distance_km": 6.7, "price_chf": 18.6, "car": {"make": "VW", "model": "Passat", "year": 2013, "co2_g_per_km": 123},
         "co2_kg": 0.82, "route": [[47.34, 8.47], "…"], "offer_id": "…"},
        {"kind": "train", "line": "S5", "from": "Hedingen", "to": "Zürich HB", "departure": "…", "arrival": "…", "platform": "1",
         "distance_km": 10.3, "co2_kg": 0.07, "route": ["…"]},
        {"kind": "transfer", "minutes": 4.0},
        {"kind": "train", "line": "IC81", "…": "…"},
        {"kind": "vertt", "from": "Bern", "to": "destination", "wait_min": 2, "…": "…"}
      ]
    }
  ],
  "comparisons": {
    "vertt_only": {"departure": "…", "arrival": "…", "distance_km": 123.6, "price_chf": 250.55, "co2_kg": 15.2, "car": {"…": "…"}},
    "public_transport_only": {"departure": "…", "arrival": "…", "transfers": 3, "price_chf": {"none": 61.0, "half": 30.5, "ga": 0.0}, "co2_kg": 1.57}
  }
}
```

| Field | Meaning |
|---|---|
| `status` | `ok`, `not_suitable` (under 10 km – show "Trip not suitable for intermodal journey"), `no_trip` (show "No trip found for this time"); `message` holds the text |
| `trips` | Only trips that carry at least one label for one of the travelcards, sorted by arrival. Show those with a label for the **chosen** travelcard |
| `price_chf` | Total per travelcard (`none`, `half`, `ga`), rounded to CHF 0.05 – switching the travelcard needs no new request |
| `labels` | Fastest / Cheapest / Greenest per travelcard; one trip can carry several |
| `legs[].kind` | `vertt` (with car, waiting time, price), `train` (line, platform), `transfer` (minutes between trains), `walk` (minutes, distance) |
| `route` | `[lat, lon]` points for the map |
| `comparisons` | The two comparison cards; `null` if one could not be calculated |

Times are Swiss local time (ISO 8601). Prices are shown as normal prices – where OJP Fare gave none, the engine estimated it (server log only).

## Errors

| HTTP | `status` | When |
|---|---|---|
| 400 | `invalid_request` | Missing field, or `departure` without time zone |
| 400 | `past_time` | Departure more than 5 min in the past – "Please choose a time in the future" |
| 429 | `too_many_searches` | OJP rate limit – "Too many searches, please wait a moment" |
