# PROJ-1-PRD-8: Trip engine

## Status: Planned – decided by Tim 2026-10-05/06, ready to code

A service of our own on the server (**Vercel**, Python), between the partner interfaces and the booking app. For every search it **builds door-to-door trips live** from the customer's start address, destination address and departure time: a Vertt ride (or a walk) to a **main station**, a train (OJP), and a Vertt ride (or a walk) to the destination. It gets the legs from SBB (PROJ-1-PRD-6) and Vertt (PROJ-1-PRD-7), calculates totals and labels, and serves the result to the booking app. Stories 27, 28, 29 (see [docs/PRD.md](../../../docs/PRD.md) section 5).

## How a search works

```
1. Customer: start address, destination address, "depart at" date + time, travelcard → "Search"
2. swisstopo: addresses → coordinates. Under 10 km apart → "Trip not suitable for intermodal journey", stop.
3. Candidate stations per side (start and destination) from config/hubs.yaml – tier rule:
     Tier 1: the best Tier 1 hub within 25 km; if there is none, the nearest Tier 1 hub (always included)
     Tier 2: the best Tier 2 hub within 25 km – only if it is closer to the address than the Tier 1 hub
     Tier 3: the best Tier 3 hub within 25 km – only if it is closer than the hubs already chosen
     best = smallest (distance from the address + detour)
4. For each combination (max. 3 × 3 = 9):
     start → station:   ≤ 1 km → walk (OJP), otherwise Vertt leg (Vertt API)
     station → station: OJP – first train leaving ≥ 8 min after arrival at the station
                        OJP Fare – half-fare price only; no travelcard = 2 × half-fare; GA = CHF 0.00
     station → dest.:   same rule as the start
     Vertt leg: pickup = chosen time + 5 min (start) / train arrival + 2 min (destination station)
5. Totals per trip: arrival time, duration, price, CO₂
6. Labels by calculation: Fastest / Cheapest / Greenest → max. 3 bookable cards
7. Comparison cards: "Vertt only" (Vertt API, whole route), "Public transport only" (OJP door to door)
```

`detour = (start → station) + (station → destination) − (start → destination)`, straight-line distances, calculated in code (no API call). "Closer" = straight-line distance from the address to the station. Distance + detour (not detour alone) is used so that a near station on the way wins over a far station that happens to lie on the route.

## Decisions (Tim, 2026-10-05/06)

| Topic | Decision |
|---|---|
| Preset trips | None. Every trip is calculated **live** for the entered addresses (needs internet and our server during the demo). |
| Recorded Vertt rides (9) | **Validation only** (PROJ-1-PRD-7 US-5). Not used in the demo. |
| Start / destination | Address fields with swisstopo suggestions, **empty** in the first version; "Search" button. No "use my location". |
| Time | Customer chooses **"depart at"** date and time. No "arrive by". |
| Short trips | Start and destination **under 10 km** apart: no search, message "Trip not suitable for intermodal journey". |
| Stations | **Main stations only**: the 70 hubs in `config/hubs.yaml` (Tier 1 national, Tier 2 regional, Tier 3 local; standard gauge, Swiss only). Smaller stations later (GitHub issue #19). |
| Candidate rule | **Tier rule** (step 3): Tier 1 always (within 25 km, else the nearest); Tier 2 only if closer than Tier 1; Tier 3 only if closer than the hubs already chosen. Within a tier: smallest distance + detour. Max. 3 per side. |
| AI model | **None in Prototype 1** (Jev dropped 2026-10-06 – see "Background"). |
| Trains per station pair | Only the **first possible train** (≥ 8 min transfer). |
| Walk instead of Vertt | At **both ends**, if the station is within **1 km** straight line. Also the minimum distance for a Vertt ride. |
| Trips without Vertt leg | Offered only if they result from the normal calculation, without extra calls. |
| Vertt tariff | **Same tariff everywhere** in Switzerland, factor 1.0. |
| Car | Drawn from the **car pool** (`config/car_pool.yaml`), once per Vertt leg. |
| Pickup | **5 min** after the chosen time at the start; **2 min** after the train arrival at the destination station. |
| Train price | Only the **half-fare** price from OJP Fare; no travelcard = 2 × half-fare, GA = CHF 0.00. Shown as normal prices. |
| Train CO₂ | The **OJP value** (EmissionCO₂ per person-km × distance). |
| Response time | Results within ~5 s, with a loading state. Partner calls run in parallel. |
| Offers shown | Only the labelled trips (max. 3) + the two comparison cards (not bookable, not clickable). |
| Hosting | **Vercel** (Python functions), behind the password gate (`mockup/middleware.js`, `DEMO_PASSWORD`). Keys are stored in Vercel. |

All values (thresholds, waiting times, radius) are configurable.

## User Stories

### US-1: As a partner app, I want one service that returns complete trip offers so that I don't have to combine the partners' leg offers myself (story 28)
**Given** start and destination address, departure time and travelcard
**When** the booking app presses "Search"
**Then** it gets up to three labelled trips and the two comparison cards in one answer

**Acceptance Criteria:**
- [ ] AC-1: The browser sends one request and gets one answer: labelled trips and comparison cards, each with all legs, totals and labels.
- [ ] AC-2: Vertt legs come only from the Vertt API (PROJ-1-PRD-7); train legs, walk legs and prices only from OJP and OJP Fare (PROJ-1-PRD-6). The engine holds no leg data of its own.
- [ ] AC-3: The answer is JSON and documented in `docs/api/trip-offers.md`.
- [ ] AC-4: Not a public service: one entrance for our own frontend, behind the password gate; requests from other websites are refused and the number of searches per visitor is limited.
- [ ] AC-5: Vertt API, OJP, OJP Fare and Valhalla are called from the server only, with secrets the browser never sees.
- [ ] AC-6: Repeating the same search gives the same result and costs no new partner calls (cache).

### US-2: As a customer, I want the right main stations to be tried so that I get a good trip, not only via the nearest station (story 29)
**Given** start and destination are known
**When** the engine looks for stations
**Then** it applies the tier rule to the hubs in `config/hubs.yaml`

**Acceptance Criteria:**
- [ ] AC-7: Per side, one Tier 1 hub is always a candidate: the best one within 25 km, or – if none is within 25 km – the nearest Tier 1 hub. "Best" = smallest distance from the address + detour.
- [ ] AC-8: The best Tier 2 hub within 25 km is added only if it is closer to the address than the chosen Tier 1 hub.
- [ ] AC-9: The best Tier 3 hub within 25 km is added only if it is closer than all hubs already chosen on that side.
- [ ] AC-10: Max. 3 candidates per side; the same station is never both start and destination candidate of one trip.
- [ ] AC-11: Reference cases (checked 2026-10-06 with `config/hubs.yaml`): Wettswil am Albis → Ostermundigen: start Zürich HB (T1, 7 km) + Hedingen (T3, 5 km), destination Bern (T1, 4 km). Uster → Bern: start Zürich HB (T1, 14 km) + Wetzikon ZH (T3, 6 km). Küssnacht am Rigi → Bellinzona: start Luzern (T1) + Arth-Goldau (T2), destination Lugano (T1) + Bellinzona (T2). Sion → Lausanne: start Sion (T2); the Tier 1 start candidate Lausanne equals the destination station and is skipped.

### US-3: As a customer, I want each candidate trip calculated with real partner data so that times, prices and CO₂ are believable
**Given** the candidate stations
**When** the engine builds the trips
**Then** every combination of start station and destination station becomes one trip

**Acceptance Criteria:**
- [ ] AC-12: Start and destination less than 10 km apart (straight line): no stations, no trips; the message "Trip not suitable for intermodal journey" is shown.
- [ ] AC-13: For each combination (max. 9), one trip is built: first leg, train, last leg. First and last leg: walk (from OJP) if the station is within 1 km straight line, otherwise a Vertt leg from the Vertt API.
- [ ] AC-14: First Vertt leg: pickup = chosen time + 5 min. Last Vertt leg: pickup = train arrival + 2 min.
- [ ] AC-15: Train leg: the first train from OJP that leaves at least 8 minutes after the arrival at the station; times, line, platform, route and distance from OJP.
- [ ] AC-16: Train price: only the half-fare price (2nd class) from OJP Fare (PROJ-1-PRD-6); no travelcard = 2 × half-fare; GA = CHF 0.00. All shown as normal prices.
- [ ] AC-17: Train CO₂ = OJP value (kg per person-km × distance).
- [ ] AC-18: A trip with a missing train price, or a leg that cannot be calculated, is not offered.
- [ ] AC-19: If both ends are walks, the trip is a train-only trip and is offered like any other.

### US-4: As a customer, I want to see the fastest, cheapest and greenest trip so that I can choose by what matters to me (story 27)
**Given** the candidate trips are calculated
**When** the connection list is shown
**Then** I see up to 3 labelled, bookable trips and the two comparison cards

**Acceptance Criteria:**
- [ ] AC-20: Totals per trip: arrival time, duration (door to door), price (sum of rounded leg prices), CO₂.
- [ ] AC-21: "Fastest" = earliest arrival; "Cheapest" = lowest total price; "Greenest" = lowest total CO₂ – calculated only. A trip that wins several labels is shown once with all of them; ties: earlier arrival, then lower price.
- [ ] AC-22: Comparison "Vertt only": one Vertt API offer for the whole route. "Public transport only": OJP door to door. Both show times, price and CO₂.
- [ ] AC-23: Changing the travelcard recalculates prices and labels from the stored half-fare price, without new partner calls.
- [ ] AC-24: Partner calls run in parallel; the list appears within ~5 s, with a loading state until then.

## Edge Cases
- No Tier 2 / Tier 3 hub closer than the Tier 1 hub: only the Tier 1 hub is tried on that side.
- Start or destination is itself a hub: it is the closest candidate; first/last leg is a walk of 0 minutes.
- Start and destination have the same Tier 1 hub (possible for trips just over 10 km): that combination is skipped; other combinations remain, otherwise "no trip found".
- A remote address with the nearest Tier 1 hub far away (e.g. 60 km): a long Vertt ride – realistic and a fair comparison.
- OJP finds no train for a station pair at the chosen time (night): that combination is skipped. All fail → "no trip found for this time".
- OJP Fare limit (50 calls/min): about 4 new searches per minute; cached searches are free; above that "Too many searches, please wait a moment" – never made-up data.
- Valhalla public server unreachable: cached answers; otherwise the Vertt leg cannot be calculated → trip not offered.
- GA: all train prices CHF 0.00 → "Cheapest" decided by the Vertt legs.

## Background
- **AI spike (2026-10-06):** Jev 1.13 (OpenRouter) chose hubs well (9 of 12 confident and correct) but nearby stations poorly – it only knew distance and detour, not which trains stop there. A simple "smallest detour" rule chose the same hub in 10 of 12 cases. Jev was therefore dropped; the tier list carries the train-service information instead. A possible later use: a "Recommended" label weighing time, price, CO₂ and transfers.

## Open Questions
- **Example address pair** to pre-fill later (e.g. Wettswil am Albis → Ostermundigen), once the engine has been tried.

## Dependencies
- Requires: `config/hubs.yaml`, swisstopo ([docs/api/geocoding.md](../../../docs/api/geocoding.md)), Valhalla ([docs/api/routing.md](../../../docs/api/routing.md)), OJP 2.0 and OJP Fare ([ojp20.md](../../../docs/api/ojp20.md), [ojpfare.md](../../../docs/api/ojpfare.md)), Vertt API (PROJ-1-PRD-7), Vercel.
- Feeds: PROJ-1-PRD-2 (connection list), PROJ-1-PRD-3 (overview), PROJ-1-PRD-5 (amounts and CO₂ per operator for the data link).

## Technical Requirements
- Python, Vercel server functions; the OJP, OJP Fare and Vertt API keys are Vercel environment variables and never appear in the page, the repo, a data link or an export.
- API calls per search are capped: max. 3 stations per side, first train only, half-fare price only. All answers are cached.
- All money, time, distance and CO₂ calculations happen in code.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- No screen of its own: its result fills the connection list (PROJ-1-PRD-2).
