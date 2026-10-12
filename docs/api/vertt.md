# Vertt API – calculated ride offers

Version **1**. Spec: PRD-7. Code: `src/vertt.py` (logic), `api/vertt/offer.py` (Vercel function).
Related: [routing.md](routing.md) (Valhalla) · [open topics](../open-topics.md)

## Overview

| | |
|---|---|
| Endpoint | `POST /api/vertt/offer` |
| Auth | Header `X-Vertt-Secret: <VERTT_API_SECRET>` – only our own server knows it. Without it: `403 not_allowed` |
| Format | JSON in, JSON out (UTF-8) |
| Read-only | Calculates offers; no booking, nothing stored about the caller |

Every offer is **calculated**: distance, ride time and street route from Valhalla, price with the Vertt tariff, CO₂ with a car drawn from `config/car_pool.yaml`.

## Request

```json
{
  "start":       {"lat": 47.3416,  "lon": 8.4708},
  "destination": {"lat": 47.37818, "lon": 8.54021},
  "pickup_time": "2026-10-13T08:05+02:00"
}
```

| Field | Meaning |
|---|---|
| `start`, `destination` | Positions in WGS84 (latitude, longitude) |
| `pickup_time` | Planned pickup, ISO 8601 with time zone. Part of the offer ID; the tariff has no time factor in Prototype 1 |

## Answer: offer

```json
{
  "version": "1",
  "status": "offer",
  "offer_id": "0a69e6a84390",
  "pickup_time": "2026-10-13T08:05+02:00",
  "distance_km": 13.506,
  "ride_time_min": 22.1,
  "price_chf": 33.93,
  "currency": "CHF",
  "factor": 1.0,
  "car_category": "Vertt",
  "car": {"make": "Renault", "model": "Talisman", "year": 2018, "co2_g_per_km": 120},
  "co2_kg": 1.621,
  "route": [[47.34162, 8.47075], "… 555 points …", [47.37819, 8.54058]],
  "assumptions": {"calculated": true, "tariff": "Vertt standard, same everywhere", "factor": 1.0, "car": "drawn from the car pool"}
}
```

| Field | Type | Meaning |
|---|---|---|
| `version` | string | API version; a change of a field name or meaning is a new version |
| `status` | string | `offer`, `not_served`, `not_allowed`, `invalid_request` |
| `offer_id` | string | Same start, destination and pickup time → same ID and same offer (incl. car) |
| `distance_km` | number | Driving distance (Valhalla) |
| `ride_time_min` | number | Ride time without waiting (Valhalla) |
| `price_chf` | number | CHF 3.00 + 1.80/km + 0.30/min, at least CHF 10.00, × factor – exact to the centime. The booking app rounds to CHF 0.05 |
| `factor` | number | Time-and-place factor, always 1.0 in Prototype 1 |
| `car` | object | Car from the car pool: make, model, year, CO₂ in g/km |
| `co2_kg` | number | `distance_km` × `co2_g_per_km` / 1000 |
| `route` | array | Street route as `[lat, lon]` points, for the map |
| `assumptions` | object | How the offer was made |

## Other answers

| Status | HTTP | When |
|---|---|---|
| `not_served` + `reason: too_short` | 200 | Start and destination less than 1 km apart (straight line) – a walk is the right answer |
| `not_served` + `reason: outside_switzerland` | 200 | A position outside Switzerland (rough box) |
| `not_served` + `reason: no_route` | 200 | Valhalla finds no route or does not answer |
| `invalid_request` | 400 | Missing or malformed field |
| `not_allowed` | 403 | Wrong or missing `X-Vertt-Secret` |

## Reference prices (tested)

| Distance | Ride time | Price |
|---|---|---|
| 10 km | 5 min | CHF 22.50 |
| 2 km | 3 min | CHF 10.00 (minimum) |
| 13.172 km | 21.2 min | CHF 33.07 |
