# Routing – distance and ride time between two positions

Status: derived from **real responses** on 2026-10-05 (trial). **Decided 2026-10-05: Valhalla.**
Related: [geocoding.md](geocoding.md) · [open topics](../open-topics.md) · PRD-7 in `specs/` (Vertt partner API)

## 1. Why it is needed

The Vertt tariff needs two numbers per ride: **distance (km)** and **ride time (minutes)**. Every Vertt leg of the demo – first leg, last leg and the "Vertt only" comparison – is calculated, so these numbers come from a route service. The same answer also gives the street route for the map. The recorded rides are used only to check the result (PRD-7).

## 2. Can swisstopo do it?

**No.** The GeoAdmin API offers address search, map data, heights and elevation profiles, but no car routing: no request returns a driving distance or a ride time between two positions (documentation searched 2026-10-05, nothing found).

## 3. Options tried

Five routes from the provided rides, asked from the **locality centre** of Wettswil am Albis (never the real address) to the station. Price = Vertt tariff applied to the answer.

| Route | Recorded rides | OSRM (public demo server) | Valhalla (public server of FOSSGIS) |
|---|---|---|---|
| Wettswil am Albis → Zürich HB | 12.9–14.1 km · 21–30 min · charged CHF 33.65–34.65 | 12.6 km · 15 min · CHF 30.20 | 12.6 km · 22 min · **CHF 32.25** |
| Zürich HB → Wettswil am Albis | 13.5–13.7 km · 17–19 min · CHF 31.00–31.30 | 12.4 km · 15 min · CHF 29.75 | 12.4 km · 22 min · **CHF 31.80** |
| Wettswil am Albis → Schlieren | 10.9 km · 15 min · CHF 23.90 | 12.7 km · 15 min · CHF 30.20 | 12.7 km · 16 min · CHF 30.65 |
| Zürich Enge → Wettswil am Albis | 11.6 km · 16 min · CHF 30.70 | 10.6 km · 13 min · CHF 26.00 | 10.6 km · 16 min · CHF 26.90 |
| Zürich Flughafen → Wettswil am Albis | 28.5 km · 24 min · CHF 66.40 (factor 1.2 → 55.35 without) | 25.5 km · 25 min · CHF 56.55 | 27.4 km · 28 min · CHF 60.50 |

Findings:
- Both answer in 0.02–0.15 s, need **no key**, cover more than Switzerland, and are based on OpenStreetMap.
- **Valhalla's ride times are closer to the real rides.** OSRM assumes empty roads and is too fast in the city (15 instead of 21–30 minutes).
- Neither knows the traffic of the moment.
- Prices land within about ±10 % of what was charged on three of five routes. The two larger gaps (Schlieren +28 %, Enge −12 %) come largely from starting at the locality centre instead of the real address – up to 2 km difference on an 11 km ride.

## 4. All options

| Option | Key | Traffic | Notes |
|---|---|---|---|
| **Valhalla** – public server of FOSSGIS | none | no | Best match in the trial. Fair use, no guarantee of availability |
| **OSRM** – public demo server | none | no | Meant for demos and tests only; ride times too short |
| **OpenRouteService** | yes (free tier) | no | Not tried. Stated daily quota; OpenStreetMap data |
| **Google Routes** | yes (paid after a free allowance) | **yes** | Not tried. Vertt's recorded routes are in Google's format, so probably what Vertt uses itself. Restrictions on storing results |
| **Vertt's own route component** | internal | ? | Would match Vertt's real prices best. To ask the CTO |
| Run Valhalla or OSRM ourselves | none | no | No limits, but something to install and host |

Because the Vertt API runs on our server and is not called from the browser (PRD-7), a key is no obstacle.

**Decided for Prototype 1:** Valhalla, with every answer stored so that a repeated demo does not depend on the public server. Switch to Vertt's own component or Google if the CTO wants prices closer to Vertt's real ones.
