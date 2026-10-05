# Prototype 1 – Intermodal Trip Records (Vertt × SBB)

Build brief for a new repository. Read this file completely before writing code.

## 1. Context

Vertt AG (Swiss ride-hailing) leads the Innovation Booster New Mobility project "Seamless Data Exchange and Payment Settlement Layer among Transport Providers (B2B)". The long-term goal is a settlement layer that bills and splits one intermodal journey (train + ride-hailing) between operators and emits a CO₂ record per segment.

Prototype 1 is the first, small step: **construct three mock intermodal trips from real data where possible, combine a Vertt ride-hailing leg with an SBB train leg from the OJP 2.0 API, and show the resulting trip records on a simple web page.**

Audience: the internal project team (not the funder, not public).

Out of scope for this prototype: smart contracts / blockchain, payment settlement, real trip capture, SBB SMAPI (commercial APIs), production deployment, publication of data.

## 2. What the prototype must produce

1. One **trip record** per mock trip (JSON), each with 2–3 segments.
2. Per segment: operator, mode, vehicle type / train, start and end coordinates, stop IDs (rail), departure and arrival time, distance, fare and fare share, CO₂ per passenger, and a data-basis flag (recorded / timetable / constructed).
3. Per trip: total passenger fare, **fare split Vertt vs SBB**, total CO₂ per passenger, transfer gaps and whether they meet the buffer window.
4. A **static web page** showing the three trips: map with all legs, timeline, fare split, CO₂ per segment, and clear labels for constructed data.
5. A short **README** documenting the architecture, how to run it, data sources and every assumption.

## 3. Inputs

### 3.1 Vertt ride data (local file, not committed)

File: `station_rides_mock_trips.xlsx` → put it in `data/raw/` and add `data/raw/` to `.gitignore`. It contains personal data (passenger ID, home addresses).

Sheets:
- `station_rides` – 9 recorded Vertt rides that start or end at a train station (2021–2023, one passenger). Relevant columns: `Ride ID`, `lat`, `lng` (pickup), `Dropoff lat`, `Dropoff lng`, `Ride Date&Time` (order time), `Passenger picked up (ride start)`, `Dropoff (ride end)`, `Actual distance driven (m)`, `Route polyline` (encoded Google polyline), `Make`, `Model`, `Year of first registration`, `Ride Price`, `Passenger Price`, `Passenger Promotion (Discount)`, `Driver Earnings Without Tip`, `Service Fee`, `ServiceFee VAT`, `station_side` (pickup/dropoff).
- `Car to CO2` – CO₂ value per vehicle, row-aligned with `station_rides`. Column header says `CO2 (g/100km)`, but values (90–134) look like g/km → treat the unit as **g/km, configurable**, and flag it in the README. Some values are missing ("No TG-Number", empty). Renault Megane 2015 appears with two values (90 and 110).
- `mock_trips` – the manually prepared trip plan (segments, times, coordinates, station IDs, transfer check). Use it as the reference for expected results.

Known data facts (verified):
- `Ride Price = Driver Earnings Without Tip + Service Fee + ServiceFee VAT` (± rounding)
- `Ride Price = Passenger Price + Passenger Promotion (Discount)`
- Timestamps have no timezone. **Assume Europe/Zurich local time**, keep it configurable (unconfirmed).

### 3.2 OJP 2.0 API (SBB / Swiss public transport journey planner)

- Endpoint: `https://api.opentransportdata.swiss/ojp20` (HTTP POST, XML body)
- Auth: API key as Bearer token. Read it from `.env` (`OJP_API_KEY=...`), never commit it. Provide `.env.example`.
- Plan limits: 20,000 calls/day, 50 calls/minute → cache all responses to disk (`data/cache/`) and add simple rate limiting.
- Docs:
  - How to access APIs: https://opentransportdata.swiss/de/cookbook/development-miscellaneous-cookbook/howto-access-apis/
  - OJP cookbook: https://opentransportdata.swiss/en/cookbook/open-journey-planner-ojp/
  - OJP 2.0 data model: https://vdvde.github.io/OJP/release/2.0/documentation-tables/ojp.html
- Requests needed:
  - `OJPLocationInformationRequest` – resolve station coordinates/names to stop references (SLOID).
  - `OJPTripRequest` – find the train leg between two stops at a given time. Request leg geometry (leg projection / track) if available for the map and the rail distance.
- Facts to respect:
  - OJP only covers the **current timetable period** → historic dates (2021–2023) cannot be queried. All trips are shifted to current dates (see 4.1).
  - OJP 2.0 does **not return fares** (`IncludeFare` is documented as not supported).
  - Stop references use **SLOID**.
  - Verify in the spec how to request trips by **arrival time** (needed for trip 2). Do not guess the XML structure – build it from the spec and test it.
- Optional, open: OJP Fare (beta, NOVA prices) at `https://api.opentransportdata.swiss/ojpfare/` – integration environment, not production data. Do not build on it unless decided (see 7).

Network note: the API was not reachable from the cloud sandboxes used so far. Run the pipeline on a machine with normal internet access.

## 4. The three mock trips

### 4.1 Construction rules

- **Vertt legs** are taken from recorded rides unchanged (duration, distance, vehicle, fare). Only the **date** is shifted to a current timetable date with the **same weekday**; the time of day stays the same.
- Mock dates: configurable. Default = next date with the matching weekday from the run date. Reference check was done for Fri 2026-10-09 (trips 1, 2) and Tue 2026-10-06 (trip 3).
- **SBB legs** come from OJP for the shifted date.
- **Transfer buffer window: 8–15 minutes** at the transfer station (configurable `buffer_min = 8`, `buffer_max = 15`).
  - Vertt → SBB: choose the first train departing ≥ dropoff + `buffer_min`. Flag if the gap > `buffer_max`.
  - SBB → Vertt: choose the latest train arriving ≤ pickup − `buffer_min`. Flag if the gap > `buffer_max`.
- Every segment carries `data_basis`: `recorded` (Vertt ride), `timetable` (OJP), `constructed` (fabricated or shifted values). A shifted date alone is noted per trip, not per field.

### 4.2 Trip definitions

| Trip | Journey | Segment | Source | Key values |
|---|---|---|---|---|
| 1 | Vertt → SBB | 1 Vertt: Wettswil am Albis → Schlieren Bahnhof | Recorded ride `05017317-febc-4aa9-9fe0-5c51f574b899` (Fri 2021-10-22) | Pickup 21:31:07, dropoff 21:46:04, 10,901 m, Renault Megane 2015, Ride Price CHF 23.90 |
| 1 | | 2 SBB: Schlieren → Mellingen Heitersberg (direct) | OJP | Reference: S11 dep 22:08, arr 22:24 |
| 2 | SBB → Vertt | 1 SBB: Winterthur → Zürich Enge (direct) | OJP | Reference: S8 dep 17:11, arr 17:42 |
| 2 | | 2 Vertt: Zürich Enge → Wettswil am Albis | Recorded ride `3d8ac3fb-74e4-40b5-bb7c-53b9c0931f5b` (Fri 2021-10-22) | Ordered 17:37:11, pickup 17:54:38, dropoff 18:11:04, 11,607 m, VW Passat 2013, Ride Price CHF 30.70 |
| 3 | Vertt → SBB → Vertt | 1 Vertt: Wettswil am Albis → Zürich HB | Recorded ride `e86e147a-3573-49dd-9287-9752ab1b9850` (Tue 2022-01-25) | Pickup 11:26:16, dropoff 11:47:27, 13,172 m, BMW 3er 2020, Ride Price CHF 33.65 |
| 3 | | 2 SBB: Zürich HB → Bern (direct) | OJP | Reference: IC 8 dep 12:02, arr 12:58 |
| 3 | | 3 Vertt: Bern Bahnhof → Ostermundigen | **Constructed** | Pickup = train arrival + buffer; dropoff address, distance, duration, vehicle and fare from config (see 7) |

Reference values come from the current Swiss timetable (transport.opendata.ch, checked 2026-10-04) and serve as a sanity check for the OJP results – they are not an input.

Reference stop IDs (UIC/DIDOK numbers, resolve SLOIDs via OJP): Schlieren 8503509, Mellingen Heitersberg 8516219, Winterthur 8506000, Zürich Enge 8503010, Zürich HB 8503000, Bern 8507000.

Known issue: trip 1 does **not** meet the 8–15 min window with the recorded time (dropoff 21:46, S11 only at :08/:38 → gap 21.9 min). Implement a per-leg config `time_shift_min` (default 0) so the Vertt leg can be shifted (e.g. +8 min → gap 13.9 min). Mark a shifted time as `constructed`. Decision pending (see 7).

## 5. Calculations

### 5.1 Fare and fare split

- Vertt segment fare = `Passenger Price` (what the passenger paid) – keep `Ride Price`, `Promotion`, `Driver Earnings`, `Service Fee`, `ServiceFee VAT` in the record as the Vertt-internal split.
- SBB segment fare = **placeholder from config** (`sbb_fares` per route, default `null`). Fare source is an open topic. If null, show "fare open" on the page and compute the split only for known parts.
- Trip fare split = share of each operator in the total passenger fare.
- Constructed Vertt leg fare: from config, until the Vertt tariff formula is provided (the export's `Base fare`, per-km 1.80 and per-minute 0.30 do not reproduce the ride price – do not derive a formula from them).

### 5.2 CO₂ per passenger

- Vertt: `distance_km × vehicle_factor_g_per_km / occupancy`, occupancy configurable (default 1 passenger). Factor from `Car to CO2`; missing factors → `null` + flag, no invented values.
- Rail: `rail_distance_km × rail_factor_g_per_pkm`. Rail distance from OJP (leg length / track). Rail factor = config placeholder (default `null`, open topic).
- Output g CO₂ per segment and per trip.

## 6. Trip record schema (v0)

This is also the first draft of the project's trip-data schema. Keep field names stable and document them in `docs/schema.md`.

```json
{
  "trip_id": "mock-1",
  "journey_type": "vertt_sbb",
  "mock_date": "2026-10-09",
  "constructed_notes": ["date shifted from 2021-10-22 (same weekday)"],
  "segments": [
    {
      "seq": 1,
      "operator": "Vertt",
      "mode": "ride_hailing",
      "data_basis": "recorded",
      "source_ref": "05017317-febc-4aa9-9fe0-5c51f574b899",
      "vehicle": {"type": "car", "make": "Renault", "model": "Megane", "year": 2015},
      "from": {"name": "Wettswil am Albis", "lat": 47.345, "lng": 8.470, "stop_ref": null},
      "to": {"name": "Schlieren", "lat": 47.399, "lng": 8.449, "stop_ref": "<SLOID>"},
      "departure": "2026-10-09T21:31:07+02:00",
      "arrival": "2026-10-09T21:46:04+02:00",
      "distance_m": 10901,
      "geometry": "<encoded polyline or GeoJSON>",
      "fare": {"currency": "CHF", "passenger_price": 19.10, "ride_price": 23.90, "promotion": 4.80,
               "driver_earnings": 19.27, "service_fee": 4.30, "service_fee_vat": 0.33},
      "co2": {"g_per_passenger": null, "factor_g_per_km": null, "factor_source": "Car to CO2 sheet", "flags": []}
    }
  ],
  "transfers": [{"at": "Schlieren", "gap_min": 21.9, "within_window": false}],
  "totals": {"passenger_fare_chf": null, "fare_split": {"Vertt": null, "SBB": null}, "co2_g_per_passenger": null}
}
```

## 7. Open decisions (keep configurable, do not hard-code a guess)

| Topic | Status | Default in code |
|---|---|---|
| Trip 1 buffer: shift Vertt leg +8 min vs accept 21.9 min gap | Pending (Tim) | `time_shift_min = 0`, flagged |
| Trip 2 anchor: train arrives before pickup or before order time (17:37) | Pending | anchor = pickup |
| Trip 3 constructed leg: Ostermundigen address, distance, duration, vehicle, fare | Pending | config placeholders, page shows "tbd" |
| Vertt tariff formula | Ask Vertt CTO | none |
| SBB fare source (OJP Fare beta / reference prices / modelled; full fare vs half-fare) | Open with SBB | `null` |
| Rail CO₂ factor per passenger-km | Open | `null` |
| CO₂ unit in `Car to CO2` (g/km vs g/100km), duplicate Megane 2015 values | To verify | g/km, flag |
| Timezone of Vertt timestamps | To verify | Europe/Zurich |
| Hosting of the page | Decide with Vertt CTO | local static build |

## 8. Privacy

The page and any committed file must not contain `passengerId` or exact home addresses. Show residential endpoints only as the locality (e.g. "Wettswil am Albis") and round their coordinates (e.g. 3 decimals) or snap them to the locality centre. Station endpoints can be exact.

## 9. Suggested setup

- Python 3.11+, `pandas`/`openpyxl` (Excel), `httpx` or `requests` (OJP), `lxml` (XML), `pydantic` (schema), `polyline` (decode Vertt route), `python-dotenv`.
- Web page: one static HTML file generated from the trip JSON (Leaflet + OpenStreetMap tiles for the map, plain HTML/CSS for timeline and tables). No backend.
- Structure:

```
config/trips.yaml        # trip definitions, buffer window, mock dates, open-decision values
data/raw/                # Excel (gitignored)
data/cache/              # OJP responses (gitignored)
data/output/             # trip records JSON
src/load_rides.py
src/ojp_client.py        # LIR + TripRequest, caching, rate limit
src/build_trips.py       # construction rules, transfer check
src/calc.py              # fare split, CO2
src/render_page.py
docs/schema.md
README.md
.env.example
```

- One command to run the whole pipeline (e.g. `python -m src.build_trips && python -m src.render_page`).

## 10. Suggested order of work

1. Repo skeleton, `.gitignore`, `.env.example`, config file.
2. Load the Excel and build the Vertt legs; unit-test the fare identities from 3.1.
3. OJP client: one `OJPLocationInformationRequest` and one `OJPTripRequest` for trip 3 (Zürich HB → Bern), save raw XML, parse departure/arrival/line/stops/distance. Compare with the reference values.
4. Arrival-time request for trip 2; departure-time request for trip 1.
5. Assemble trip records, transfer check, constructed leg for trip 3.
6. Fare split and CO₂ with the placeholders.
7. Static page.
8. README with assumptions and open decisions.

## 11. Acceptance criteria

- Pipeline runs end to end with one command and an API key in `.env`.
- Three trip records are written as JSON and validate against the schema.
- OJP train legs match the timetable reference values (or differences are explained, e.g. timetable change).
- Transfer gaps are computed and checked against the 8–15 min window; violations are visible.
- Every constructed or placeholder value is labelled in the JSON and on the page.
- No personal data in committed files or on the page.
- README documents data sources, assumptions and the open decisions from section 7.
