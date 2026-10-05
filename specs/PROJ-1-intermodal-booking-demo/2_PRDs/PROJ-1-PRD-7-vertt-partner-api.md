# PROJ-1-PRD-7: Vertt partner API

## Status: Planned

Vertt gets its own interface, the counterpart to OJP on the SBB side: a partner asks it what a Vertt ride from position A to position B at a given time looks like and costs. Every offer is **calculated**: distance, ride time and route from the route service **Valhalla**, price with the **Vertt tariff**, CO₂ with a car drawn from the **car pool**. It is a building block for the later prototypes; Vertt's real price engine can later replace what is behind it without changing the interface. Source: [docs/user-stories.md](../../../docs/user-stories.md) stories 24, 25, 26; trip engine [PROJ-1-PRD-9](PROJ-1-PRD-9-trip-engine.md).

## The Vertt tariff

Source: Vertt's tariff engine specification (PROJ-11 in Vertt's discovery repository, verified against Vertt's price documentation, Zurich rates). Reviewed 2026-10-05. This answers the question "what is the Vertt tariff formula" (cto-meeting T2, question 1; GitHub issue #11). Publishing these values in this public repo: approved 2026-10-05.

**Price = (initial price + distance × price per km + ride time × price per minute), at least the minimum price, × time-and-place factor**

| Part | Service class "Standard" (called "Vertt" in the export) |
|---|---|
| Initial price | CHF 3.00 |
| Price per km | CHF 1.80 |
| Price per minute of ride time (waiting is not charged) | CHF 0.30 |
| Minimum price | CHF 10.00 – applied before the factor |
| Time-and-place factor | 1.0 normally; higher at defined peak times in defined Zurich zones (up to 2.0). **Prototype 1: always 1.0** (decided 2026-10-05) |

More rules from the same specification that matter here:
- The price shown before the ride is calculated from the **estimated** distance and time. It is also the price charged, unless the real ride differs very strongly from the estimate.
- The price does not depend on the driver or the car.
- A higher class "Premium" exists with its own values (story 7 mentions it as a later option).
- Promotions are not part of the tariff; a discount is applied afterwards.
- Cancellation and no-show: CHF 0.00 in the new platform's first phase (the old system charged CHF 6.00 for a late cancellation). This supports the demo rule "full refund, no fee" on the Vertt side.

**Prototype 1 assumption (decided by Tim 2026-10-05, to confirm with CTO):** the Zurich values apply to every Vertt leg in Switzerland.

## Validation with the recorded rides

The Excel export in `data/raw/` (not in Git, contains personal data) holds 9 finished rides, 2021–2023, all of one passenger, each connecting Wettswil am Albis with a station. They are **not offers** any more – they are used once to check the calculator (PROJ-1-PRD-9 US-5).

What is known already: the tariff, applied to the **recorded** distance and ride time, gives the export's "Base fare" within CHF 0.05 for 7 of the 9 rides (the two rides from 2021 differ by about CHF 0.55). The **charged** "Ride Price" differs from it by −12 % to +7 %, because it was calculated before the ride from estimated distance and time.

Still to check (US-5): how close **Valhalla's** distance and time come to the recorded ones, and so how close a calculated offer comes to the real price.

## The car pool

A list of cars maintained by Tim in `config/car_pool.yaml`: make, model, year, CO₂ factor (g/km). It includes the cars of the recorded rides and may include more. **Every car has a CO₂ factor** (no gaps). No number plates, no vehicle IDs.

## User Stories

### US-1: As a partner app, I want a ride offer for any start and destination position so that I can show and price the Vertt leg without knowing how Vertt works inside (story 24)
**Given** two positions in Switzerland and a planned pickup time
**When** I ask the Vertt API for an offer
**Then** I get the ride with distance, duration, price, car and CO₂ factor
**And** the route to draw on the map

**Acceptance Criteria:**
- [ ] AC-1: Request: start position, destination position (latitude, longitude) and planned pickup time.
- [ ] AC-2: The offer contains: offer ID, start, destination, distance (km), ride time (min), price in CHF, factor used, car category ("Vertt"), car (make, model, year), CO₂ factor (g/km), route line.
- [ ] AC-3: Distance, ride time and route line come from **Valhalla** (car profile) for exactly the two positions.
- [ ] AC-4: The car is drawn from the car pool. Asking twice with the same offer ID returns the same offer, car included.
- [ ] AC-5: Every offer says it is **calculated** and names its assumptions: tariff region (Zurich values), factor 1.0, car drawn from the pool.
- [ ] AC-6: The offer has no fixed timetable: it gives a ride time; the trip engine places it before or after the train and adds the waiting time for the car (PROJ-1-PRD-9).
- [ ] AC-7: Positions outside Switzerland, or positions Valhalla cannot route between: a clear "not served" answer. No price is guessed.
- [ ] AC-8: Start and destination are the same, or closer than a minimum distance: "not served" (a walk is the right answer, PROJ-1-PRD-9).

### US-2: As Vertt, I want the price in an offer to follow one clear rule so that partners and the settlement work with the right amount (story 24)
**Given** an offer's distance and ride time
**When** the offer price is set
**Then** it follows the Vertt tariff

**Acceptance Criteria:**
- [ ] AC-9: Price = CHF 3.00 + CHF 1.80 per km + CHF 0.30 per minute of ride time.
- [ ] AC-10: A price below CHF 10.00 is raised to CHF 10.00.
- [ ] AC-11: The result is multiplied by the factor – 1.0 in Prototype 1. The offer names the factor.
- [ ] AC-12: Reference cases: 10 km and 5 min → CHF 25.50. 2 km and 3 min → CHF 7.50, raised to CHF 10.00. 13.172 km and 21.2 min → CHF 33.05.
- [ ] AC-13: The price does not depend on the car.
- [ ] AC-14: The offer contains no tip, no waiting charge and no discount. Promo codes are applied by the booking app (PROJ-1-PRD-3).
- [ ] AC-15: The offer contains no internal split of the price (driver earnings, service fee). Vertt is one party.
- [ ] AC-16: The price is in CHF; the booking app rounds customer prices to CHF 0.05 (story 8).

### US-3: As an IB partner, I want the Vertt API to be documented and stable so that we can use it in the later prototypes (story 25)
**Given** I want to build on the Vertt API
**When** I read its description
**Then** I find every request and every field explained, with an example

**Acceptance Criteria:**
- [ ] AC-17: `docs/api/vertt.md` describes every request and every field, with type, meaning and one example answer, in the same style as the OJP documents.
- [ ] AC-18: Every answer of the API matches the description.
- [ ] AC-19: The API answers in JSON and carries a version; a change of a field name or meaning is a new version.
- [ ] AC-20: The demo gets its Vertt data only through this API – the trip engine calls it.

### US-4: As Vertt, I want only our own app to reach the Vertt API so that the tariff and the offers are not open to everyone (decided 2026-10-05)
**Given** the Vertt API is running
**When** anything other than the server side of our own app calls it
**Then** the call is refused

**Acceptance Criteria:**
- [ ] AC-21: The Vertt API is called only by the server side of our app (PROJ-1-PRD-8). The page in the customer's browser never calls it directly.
- [ ] AC-22: A call without the valid secret is refused with a clear "not allowed" answer and reveals no data.
- [ ] AC-23: The secret never appears in the page, the repo, a data link or an export.
- [ ] AC-24: Partners get the description of the API (US-3), but no access of their own in Prototype 1.

### US-5: As the CTO, I want the calculator checked against the recorded rides so that I can trust the Vertt prices (story 26, PROJ-1-PRD-9 US-5)
**Given** the 9 recorded rides (local Excel, never committed)
**When** the calculator runs on their start and end points
**Then** calculated and recorded distance, time and price are compared

**Acceptance Criteria:**
- [ ] AC-25: A one-off script computes per ride: Valhalla distance and time vs. recorded; tariff price on Valhalla values vs. "Base fare" and vs. charged price.
- [ ] AC-26: The result is documented as deviations in % in `docs/api/routing.md` – without addresses, dates, ride IDs or anything that leads to the passenger.
- [ ] AC-27: The Excel export is never committed, deployed or used by the running API.

## Edge Cases
- A very short ride: the minimum price applies (AC-10).
- A very long ride (e.g. "Vertt only" Wettswil am Albis → Bern, about 130 km): no long-distance discount, so the price is simply high (roughly CHF 260–270). That is the intended comparison.
- Valhalla's public server is unreachable: stored answers are used; otherwise "not served" for this request – no price is guessed.
- A position is in a place a car cannot reach (pedestrian zone, lake): Valhalla snaps to the nearest road; if that is far away, "not served".
- The pool car is electric: CO₂ factor 0 – a real value.
- A call arrives with a wrong or missing secret, or straight from a browser: refused (AC-22).

## Open Questions
- **Tariff outside Zurich** and **factor 1.0** everywhere: decided for Prototype 1, to confirm with CTO.
- **Rounding.** Vertt's specification keeps prices exact to CHF 0.01 and rounds to CHF 0.05 only for cash; the demo rounds every customer price to CHF 0.05 (story 8). Keep the demo rule? → Tim.
- **VAT.** Whether the tariff values include VAT, and the rate, are open in Vertt's own specification too (8.1 % assumed there). → Vertt finance.
- **CO₂ unit** of the recorded car values (g/km vs g/100km) and the duplicate car model (GitHub issue #14) – matters for the car pool. → Tim / Vertt.
- ~~Minimum distance for a Vertt ride (AC-8)~~ → **Decided:** 1 km straight line, the walk threshold of PROJ-1-PRD-9.
- Is "book a ride" / "cancel a ride" through the API wanted later (Prototype 2)? Not part of this PRD.

## Dependencies
- Requires: Valhalla ([docs/api/routing.md](../../../docs/api/routing.md)), car pool (`config/car_pool.yaml`).
- Feeds: PROJ-1-PRD-9 (Vertt legs of every trip and the "Vertt only" comparison), PROJ-1-PRD-2 (Vertt legs, car, CO₂, map), PROJ-1-PRD-4 (Vertt part of the settlement), PROJ-1-PRD-5 (offer ID and assumptions in the data link).
- Supersedes: GitHub issues #8, #9, #10, #15 (no preset trips, no recorded legs); #11 (tariff formula) is answered by the tariff.

## Technical Requirements
- Read-only: the API calculates offers. It takes no bookings and stores nothing about the caller.
- Reachable only from the server side of our own app, with a secret (US-4); answers in JSON.
- Valhalla answers are cached, so a repeated search does not depend on the public server.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: no screen of its own. Its values appear in the Vertt leg rows and the map (PROJ-1-PRD-2).
- New component candidates: none.
- Design tokens: none.
- Interaction contract: none.
- Implementation tolerance: field names are free until `docs/api/vertt.md` exists; afterwards they are fixed (AC-19).
