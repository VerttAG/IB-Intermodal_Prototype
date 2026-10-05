# IB Intermodal Prototype 1 – Booking & Settlement Data Demo (Vertt × SBB)

A clickable booking demo for the Innovation Booster project "Seamless Data Exchange and Payment Settlement Layer among Transport Providers". For any two Swiss addresses it builds a door-to-door trip live – a **Vertt** ride to a station, an **SBB** train, a Vertt ride to the destination – shows price and CO₂ per carrier, and produces the **B2B settlement data** (who owes whom) for the partners' transaction layer.

> Status: specification done (PRD v0.5), not yet built. A lite mockup with made-up data is in `mockup/`.

## Where to find what

| Path | Content |
|---|---|
| [docs/PRD.md](docs/PRD.md) | **Start here.** Why, for whom, how it works, customer flow, story list, settlement rules, data output, scope |
| [specs/PROJ-1-intermodal-booking-demo/2_PRDs/](specs/PROJ-1-intermodal-booking-demo/2_PRDs/) | Feature specs with user stories and acceptance criteria: PRD-1 inputs · PRD-2 connections · PRD-3 login and checkout · PRD-4 settlement and cancellation · PRD-5 data link and export · PRD-6 SBB data · PRD-7 Vertt API · PRD-8 trip engine and AI |
| [docs/open-topics.md](docs/open-topics.md) | What is still open (CTO, Vertt finance, partners, spikes) |
| [docs/api/](docs/api/) | Reference for the external APIs, from real test calls |
| [mockup/](mockup/) | Lite clickable mockup (`index.html`) and the password gate for Vercel (`middleware.js`) |

## Which API does what

| Function | API | Key | Reference |
|---|---|---|---|
| Address → coordinates (suggestions while typing) | swisstopo GeoAdmin search | none | [geocoding.md](docs/api/geocoding.md) |
| Stations, train connections, walk legs, train CO₂ | OJP 2.0 (opentransportdata.swiss) | `OJP_API_KEY` | [ojp20.md](docs/api/ojp20.md) |
| Train price (half-fare) | OJP Fare (beta) | `OJP_FARE_API_KEY` | [ojpfare.md](docs/api/ojpfare.md) |
| Vertt leg: distance, ride time, street route | Valhalla (public server) | none | [routing.md](docs/api/routing.md) |
| Vertt leg: price, car, CO₂ | Vertt API (ours, to build) – Vertt tariff + car pool | server secret | PRD-7 |
| Candidate stations | Jev 1.13 via OpenRouter | `OPENROUTER_API_KEY` | PRD-8 |
| Map | Leaflet + OpenStreetMap tiles | none | – |
| Hosting, data behind the links | Vercel (password gate `DEMO_PASSWORD`) | Vercel account | PRD-5, PRD-8 |

Keys live in `.env` locally and in the Vercel project settings online – never in the repo.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # then put your keys into .env
```

The recorded Vertt rides (`station_rides_mock_trips.xlsx`) are only used locally to validate the price calculator. Put the file into `data/raw/` – it is gitignored and must never be committed (personal data).

## Run

_To be added once the build starts._
