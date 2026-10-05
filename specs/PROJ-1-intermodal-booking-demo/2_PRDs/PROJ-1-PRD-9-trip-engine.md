# PROJ-1-PRD-9: Trip engine – door-to-door trips calculated live

## Status: Planned – decided by Tim 2026-10-05, to be confirmed with CTO

Every trip is **built live** from the customer's start address, destination address and departure time. There are no preset trips any more. A trip is a Vertt ride (or a walk) to a train station, a train with OJP, and a Vertt ride (or a walk) from the arrival station to the destination. Vertt legs are **calculated**: route from Valhalla × Vertt tariff, CO₂ from a car of the car pool. The AI model only proposes **which stations are worth trying**; every label is decided by calculation.

**This PRD changes earlier specs** (details in "Changes to other specs" at the end): PROJ-1-PRD-7 (Vertt API calculates offers instead of serving recorded rides), PROJ-1-PRD-8 (the model proposes stations instead of choosing labels), PROJ-1-PRD-1 and PROJ-1-PRD-2 (any address, chosen time, car from the pool).

## How a search works

```
1. Customer: start address, destination address, "depart at" date + time, travelcard
2. swisstopo: addresses → coordinates
3. Candidate stations, separately for start and destination – max. 3 per side:
     • 1 hub station (e.g. Zürich HB, Bern, Winterthur) if one is within ~30 km
     • 2 nearby stations that make sense for the route (direction of travel, good connections)
     → proposed by the AI model (Jev), checked against OJP; code fills up with the nearest stations
4. For each combination (max. 3 × 3 = 9):
     start → station:   ≤ walk threshold → walk (OJP), otherwise Vertt leg
     station → station: OJP – first train leaving ≥ 8 min after arrival at the station
                        OJP Fare – price for the travelcard (GA = CHF 0.00)
     station → dest.:   same rule as the start
     Vertt leg = Valhalla (km, min) → tariff 3.00 + 1.80/km + 0.30/min, min. 10.00, factor 1.0
                 CO₂ = km × factor of a car drawn from the car pool
                 pickup = previous point in time + assumed waiting time
5. Totals per trip: arrival time, duration, price, CO₂
6. Labels by calculation: Fastest / Cheapest / Greenest → max. 3 bookable cards
7. Comparison cards: "Vertt only" (Valhalla whole route × tariff), "Public transport only" (OJP door to door)
```

## Decisions (Tim, 2026-10-05)

| Topic | Decision |
|---|---|
| Preset trips | Dropped. Every trip is calculated live for the entered addresses. |
| When calculated | **Live** for every search (needs internet and our server during the demo). |
| Recorded Vertt rides (9) | **Validation only**: used once to check Valhalla + tariff against reality. Not used in the demo. |
| Start / destination | Address field, typing allowed, swisstopo suggestions, pre-filled with a working example. No "use my location". |
| Time | Customer chooses **"depart at"** date and time. No "arrive by". |
| Candidate stations | Max. **3 per side**: 1 hub within ~30 km + 2 nearby stations that make sense for the route. |
| AI model | Proposes candidate stations; the code checks each against OJP. Does **not** decide labels. |
| Trains per station pair | Only the **first possible train** (≥ 8 min transfer). |
| Walk instead of Vertt | At **both ends**, if the station is within the walk threshold. |
| Trips without Vertt leg | Offered only if they result from the normal calculation, without extra AI or API calls. |
| Vertt tariff | Zurich tariff for every Vertt leg in Switzerland, **no peak factor** (1.0) – marked as assumption, to confirm with CTO. |
| Car | Drawn from the **car pool** (maintained by Tim, includes the cars of the recorded rides). |
| Pickup | Chosen departure time (or train arrival) + **assumed waiting time**. |
| Offers shown | Only the labelled trips (max. 3); other candidates are not shown. |
| Comparison cards | Both stay: "Vertt only" and "Public transport only"; not bookable, not clickable. |

## User Stories

### US-1: As a customer, I want to enter any start and destination address so that I get a door-to-door trip for exactly my journey
**Given** I am on step 1
**When** I type a start and a destination address and choose a date and time
**Then** trips are calculated for exactly these addresses

**Acceptance Criteria:**
- [ ] AC-1: Start and destination are address fields with suggestions from swisstopo while typing; both are pre-filled with a working example.
- [ ] AC-2: The chosen address is turned into coordinates by swisstopo; nothing else about the address is used.
- [ ] AC-3: Addresses outside Switzerland or not found: a clear message, no trip.
- [ ] AC-4: Date and time are chosen as "depart at"; default is the next full quarter hour. Only dates in the current timetable period are possible.
- [ ] AC-5: The typed address is not stored, logged or put into the data link (story 21); only the locality is kept for display.

### US-2: As a customer, I want sensible stations to be tried so that I get a good trip even if the nearest station is not the best one
**Given** start and destination are known
**When** the engine looks for stations
**Then** it tries up to 3 stations per side, including a hub and stations that make sense for the route

**Acceptance Criteria:**
- [ ] AC-6: Per side, at most 3 candidate stations: 1 hub station if one lies within the hub radius (~30 km), plus 2 nearby stations that make sense for the direction of travel.
- [ ] AC-7: The AI model (Jev 1.13 via OpenRouter, PROJ-1-PRD-8) proposes the candidates. It receives only the **locality** or **rounded coordinates** (≤ 2 decimals ≈ 1 km) of start and destination, never the typed address or anything about the customer.
- [ ] AC-8: Every proposed station is checked against OJP (it exists, has train service). Stations that fail the check are dropped.
- [ ] AC-9: If the model proposes fewer than 3 valid stations, does not answer in time, or is unreachable, the code fills up with the nearest stations with train service. A search never fails because of the model.
- [ ] AC-10: The data link stores which stations were candidates and whether each came from the model or from the code fallback.

### US-3: As a customer, I want each candidate trip calculated with real partner data so that times, prices and CO₂ are believable
**Given** the candidate stations
**When** the engine builds the trips
**Then** every combination of start station and destination station becomes one trip

**Acceptance Criteria:**
- [ ] AC-11: For each combination (max. 9), one trip is built: first leg, train, last leg.
- [ ] AC-12: First and last leg: if the station is within the walk threshold of the address, the leg is a walk (from OJP); otherwise it is a Vertt leg.
- [ ] AC-13: Vertt leg: distance and ride time from Valhalla; price = CHF 3.00 + CHF 1.80 per km + CHF 0.30 per minute, at least CHF 10.00, factor 1.0 (PROJ-1-PRD-7 AC-12).
- [ ] AC-14: Vertt leg CO₂ = distance in km × CO₂ factor of a car drawn from the car pool. The car is drawn once per Vertt leg and stays the same for the whole run.
- [ ] AC-15: First Vertt leg: pickup = chosen departure time + assumed waiting time. Last Vertt leg: pickup = train arrival + assumed waiting time.
- [ ] AC-16: Train leg: the first train from OJP that leaves at least 8 minutes after the arrival at the station. Times, line, platform, route geometry and distance from OJP.
- [ ] AC-17: Train price from OJP Fare for "no travelcard" or "half-fare", 2nd class (PROJ-1-PRD-6). GA = CHF 0.00 by the demo's own rule.
- [ ] AC-18: Train CO₂ as decided in CTO topic B7 (tailpipe rule 0.0 kg, or OJP value). The OJP value is always stored in the data link.
- [ ] AC-19: A trip with a missing train price, or a leg that cannot be calculated, is not offered.
- [ ] AC-20: If both ends are walks, the trip is a train-only trip. It is offered like any other trip, because it costs no extra calls.

### US-4: As a customer, I want to see the fastest, cheapest and greenest trip so that I can choose by what matters to me
**Given** the candidate trips are calculated
**When** the connection list is shown
**Then** I see up to 3 labelled, bookable trips and the two comparison cards

**Acceptance Criteria:**
- [ ] AC-21: Totals per trip: arrival time, duration (door to door), price (sum of rounded leg prices), CO₂.
- [ ] AC-22: "Fastest" = earliest arrival; "Cheapest" = lowest total price; "Greenest" = lowest total CO₂. Labels are decided by calculation only.
- [ ] AC-23: A trip that wins several labels is shown once with all its labels. Other candidate trips are not shown.
- [ ] AC-24: Ties: earlier arrival first, then lower price.
- [ ] AC-25: Comparison card "Vertt only": Valhalla for the whole route × tariff, CO₂ with a pool car. Card "Public transport only": OJP door to door. Both show times, price and CO₂; neither is bookable or clickable.
- [ ] AC-26: Changing the travelcard updates train prices and labels without recalculating routes or asking the model again.

### US-5: As the CTO, I want the calculator checked against real rides so that I can trust the Vertt prices
**Given** the 9 recorded Vertt rides (local Excel, never committed)
**When** the calculator is run on their start and end points
**Then** the calculated distance, time and price are compared with the recorded ones

**Acceptance Criteria:**
- [ ] AC-27: A one-off check computes, per recorded ride: Valhalla distance and time vs. recorded, tariff price vs. recorded "Base fare" and charged price.
- [ ] AC-28: The result is documented as deviations in % (no personal data, no addresses, no dates) in `docs/api/routing.md` or a validation note.

## Edge Cases
- No hub within the hub radius: 3 nearby stations instead.
- Start and destination are close to each other (e.g. < 5 km): no sensible train trip; only the comparison cards, or a message. → see open questions.
- Start or destination is itself a station: walk leg of 0 minutes, i.e. no first/last leg.
- The model proposes a station that does not exist, has no trains, or is very far away: dropped by the check (AC-8).
- OJP finds no train for a station pair at the chosen time (night): that combination is skipped.
- All combinations fail: clear message "no trip found for this time".
- OJP or OJP Fare limit reached (50 calls/min): cached answers are used; otherwise a clear message, never made-up data.
- Valhalla public server unreachable: cached answers; otherwise the Vertt leg cannot be calculated → trip not offered.
- Car pool car without CO₂ value: must not happen – every pool car needs a CO₂ factor (data rule).
- GA: all train prices CHF 0.00 → "Cheapest" decided by the Vertt legs.

## Open Questions
- **Walk threshold:** 1 km straight line (≈ 12 min walk)? Proposed: 1 km, configurable. → Tim.
- **Waiting time for the Vertt car:** proposed 5 min, configurable, marked as assumption. → Tim.
- **Hub list:** which stations count as hubs (e.g. Zürich HB, Bern, Basel SBB, Winterthur, Luzern, Lausanne, Genève, St. Gallen)? → Tim.
- **Start and destination very close** (e.g. same town): show only "Vertt only" + "Public transport only", or a message? → Tim.
- **Train CO₂ on screen** (CTO topic B7): 0.0 kg (tailpipe) or the OJP value?
- **Vertt tariff outside Zurich** and **no peak factor**: confirm with CTO (PROJ-1-PRD-7).
- **Response time:** up to 9 OJP + 9 OJP Fare + several Valhalla calls + 1 model call per search. Target: list within ~5 s, with a loading state. Acceptable? → Tim.
- **Data sent to OpenRouter** (rounded location, station names) leaves Switzerland – OK for Vertt and partners? → CTO (PROJ-1-PRD-8).

## Dependencies
- Requires: swisstopo address search (`docs/api/geocoding.md`), Valhalla (`docs/api/routing.md`), OJP 2.0 and OJP Fare (`docs/api/ojp20.md`, `docs/api/ojpfare.md`), Vertt tariff (PROJ-1-PRD-7), car pool (`config/car_pool.yaml`, maintained by Tim), OpenRouter access (PROJ-1-PRD-8).
- Feeds: PROJ-1-PRD-2 (connection list), PROJ-1-PRD-3 (overview), PROJ-1-PRD-5 (data link: candidates, sources, assumptions).
- Needs a server (keys for OJP, OJP Fare, OpenRouter must not reach the browser) → CTO topic T1 / hosting; password gate (`mockup/middleware.js`).

## Technical Requirements
- All keys stay on the server; the browser calls one entrance of our own (PROJ-1-PRD-8 AC-12a–c).
- API calls per search are capped: max. 3 stations per side, first train only. All answers are cached so a repeated search costs no calls.
- All money, time and CO₂ calculations happen in code, never in the model.
- Every assumption (tariff region, factor 1.0, waiting time, pool car, walk threshold) is configurable and stored with each trip in the data link.

## Changes to other specs

| Spec | Change |
|---|---|
| PROJ-1-PRD-1 | Address fields with typing (no dropdown), "depart at" date and time chosen by the customer, no "use my location". Place lists and the known-places snap no longer apply. |
| PROJ-1-PRD-2 | Connection list = up to 3 labelled trips + 2 comparison cards (not clickable). Car comes from the car pool (drawn per Vertt leg), not from a recorded ride. |
| PROJ-1-PRD-7 | The Vertt API **calculates** every offer (Valhalla + tariff + pool car). Recorded rides are no longer offers; they serve only to validate the calculator (US-5). Open questions on recorded-route prices and several rides per route no longer apply. |
| PROJ-1-PRD-8 | The model **proposes candidate stations** (US-2) instead of choosing the labels. Labels are calculated (US-4). The trial results and the privacy rules (AC-15) still apply. |
| PRD v0.3 / user stories | Preset trips and scenario times dropped; time chosen by the customer; car pool drawn per Vertt leg. |
