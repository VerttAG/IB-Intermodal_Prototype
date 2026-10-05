# PROJ-1-PRD-7: Vertt partner API

## Status: Planned

> **Changed by [PROJ-1-PRD-9](PROJ-1-PRD-9-trip-engine.md) (Tim, 2026-10-05):** the API **calculates every offer** for the exact positions it receives: distance and time from Valhalla, price with the Vertt tariff (Zurich values everywhere, factor 1.0 – to confirm with CTO), CO₂ with a car from the car pool. The recorded rides are **no longer offers**; they are used only once to validate the calculator (PRD-9 US-5). Open questions on prices of recorded routes and on several rides per route no longer apply. The tariff section and the privacy rules below remain valid. Where this PRD differs, PRD-9 wins.

Vertt gets its own interface, the counterpart to OJP on the SBB side: a partner asks it which places Vertt serves and what a ride between two places looks like and costs. It is built from the recorded rides Vertt provided and is a building block for the later prototypes. Source: [docs/user-stories.md](../../../docs/user-stories.md) stories 24, 25, 26 (proposed, v1.1).

## What the provided data contains

Reviewed on 2026-10-05: the Excel export in `data/raw/` (not in Git, contains personal data).

| Fact | Consequence for the API |
|---|---|
| 9 finished rides, 2021–2023, all of **one** passenger, car category "Vertt" | Small and easy to trace to a person → strict privacy rules (US-5) |
| Every ride connects **Wettswil am Albis** with a station | The API can only serve these routes (table below) |
| Per ride: distance, pickup and dropoff time, route line, car (make, model, year), price parts | Enough for distance, duration, map, car and price of an offer |
| CO₂ value for 6 of 9 cars; 3 are missing; one car model has two values (90 and 110); unit unclear (GitHub issue #14) | CO₂ is "not available" for some offers |
| Rides have a gross price and a price after a past discount; one ride has a surge factor and a tip | The API price rule must say which price counts (US-3) |
| The export's rates (1.80 per km, 0.30 per min) do not reproduce the **charged** price – but together with the rest of the Vertt tariff they reproduce the export's "Base fare" column (next section) | Prices can be **calculated** for any route |

Routes with recorded rides:

| From | To | Rides | Price range (CHF) |
|---|---|---|---|
| Wettswil am Albis | Zürich HB | 4 | 33.65 – 34.65 |
| Zürich HB | Wettswil am Albis | 2 | 31.00 – 31.30 |
| Wettswil am Albis | Schlieren (station) | 1 | 23.90 |
| Zürich Enge (station) | Wettswil am Albis | 1 | 30.70 |
| Zürich Flughafen | Wettswil am Albis | 1 | 66.40 (with surge) |

## The Vertt tariff

Source: Vertt's tariff engine specification (PROJ-11 in Vertt's discovery repository, verified against Vertt's price documentation, Zurich rates). Reviewed 2026-10-05. This answers the question "what is the Vertt tariff formula" (cto-meeting T2, question 1; GitHub issue #11).

**Price = (initial price + distance × price per km + ride time × price per minute), at least the minimum price, × time-and-place factor**

| Part | Service class "Standard" (called "Vertt" in the export) |
|---|---|
| Initial price | CHF 3.00 |
| Price per km | CHF 1.80 |
| Price per minute of ride time (waiting is not charged) | CHF 0.30 |
| Minimum price | CHF 10.00 – applied before the factor |
| Time-and-place factor | 1.0 normally; higher at defined peak times in defined Zurich zones (up to 2.0). The highest factor that applies at the pickup place and pickup time counts |

More rules from the same specification that matter here:
- The price shown before the ride is calculated from the **estimated** distance and time. It is also the price charged, unless the real ride differs very strongly from the estimate.
- The price does not depend on the driver or the car.
- A higher class "Premium" exists with its own values (story 7 mentions it as a later option).
- Promotions are not part of the tariff; a discount is applied afterwards.
- Cancellation and no-show: CHF 0.00 in the new platform's first phase (the old system charged CHF 6.00 for a late cancellation). This supports the demo rule "full refund, no fee" on the Vertt side.

**Checked against the provided rides:** the formula, applied to the real distance and ride time, gives the export's "Base fare" within CHF 0.05 for 7 of the 9 rides (all rides from 2022 and 2023, including the one with factor 1.2). The two rides from 2021 differ by about CHF 0.55 (2 %). The **charged** "Ride Price" differs from it by −12 % to +7 %, because it was calculated before the ride from the estimated distance and time.

## User Stories

### US-1: As a partner app, I want to ask Vertt which places it serves so that I only offer journeys Vertt can drive (story 24)
**Given** I use the Vertt API
**When** I ask for the served places
**Then** I get the list of places with name, kind and position
**And** I can see between which places a ride is possible

**Acceptance Criteria:**
- [ ] AC-1: The API returns all places that occur as start or end of a ride in the data, each with a stable ID, name, kind (locality or station) and coordinates.
- [ ] AC-2: A station carries the official stop ID, so that it can be matched with the SBB data (PROJ-1-PRD-6).
- [ ] AC-3: The API tells which from → to combinations it can serve.
- [ ] AC-4: A locality is given as the place name and one position for the whole locality, never as an address.

### US-2: As a partner app, I want a ride offer for a start and a destination so that I can show and price the Vertt leg without knowing how Vertt works inside (story 24)
**Given** two places Vertt serves
**When** I ask for an offer from one to the other
**Then** I get the ride with distance, duration, price, car and CO₂
**And** the route to draw on the map

**Acceptance Criteria:**
- [ ] AC-5: An offer contains an offer ID, from, to, distance, duration, price in CHF, car category, car (make, model, year), CO₂ factor, and the route line.
- [ ] AC-6: Distance, duration, route and car come from a recorded ride on this route and direction.
- [ ] AC-6a: If several recorded rides exist for a route, the API returns one offer per ride. Choosing among them is the job of the trip offer middleware (PROJ-1-PRD-8).
- [ ] AC-7: The request says when the pickup is planned, because the price can depend on the time (AC-12b). The offer itself has no fixed timetable: it gives a duration, and the app places the ride before or after the train.
- [ ] AC-8: The offer says how its values came about: **recorded** (distance, duration, route and car from a real ride) or **calculated** (distance, duration and route from a route calculation).
- [ ] AC-8a: For a start and destination without a recorded ride, the API returns a calculated offer, as long as both lie in the area Vertt serves. This makes a second Vertt leg at the destination and the "Vertt only" comparison possible.
- [ ] AC-8b: A calculated offer has no real car. Its car – and with it the CO₂ factor – is taken from the cars in the provided data and marked as assumed.
- [ ] AC-9: If the CO₂ factor of the car is unknown, the offer says so; it does not contain 0.
- [ ] AC-10: For a combination Vertt does not serve, the API answers clearly "not served"; it never returns an estimate without marking it.
- [ ] AC-11: Asking twice with the same offer ID returns the same offer.
- [ ] AC-11a: Start and destination of an offer request can be given as coordinates (latitude, longitude) instead of a place ID.
- [ ] AC-11b: For coordinates, the API uses the nearest place Vertt serves and says in its answer which place it used and how far it is from the coordinates.
- [ ] AC-11c: If the nearest served place is farther away than the maximum distance, the answer is "not served" (AC-10).
- [ ] AC-11d: If a route can be calculated from the given coordinates, the offer is a calculated one for exactly this position (AC-8a) and its price follows the tariff. Only if no route can be calculated does the API fall back to the nearest served place (AC-11b), and then says that the price belongs to that place.
- [ ] AC-11e: The API does not store or log the coordinates it receives, and no answer repeats them.

### US-3: As Vertt, I want the price in an offer to follow one clear rule so that partners and the settlement work with the right amount (story 24)
**Given** a recorded ride behind an offer
**When** the offer price is set
**Then** it is the full ride price, without tip and without a past discount

**Acceptance Criteria:**
- [ ] AC-12: The offer price is calculated with the Vertt tariff from the offer's distance and duration: CHF 3.00 + CHF 1.80 per km + CHF 0.30 per minute.
- [ ] AC-12a: A calculated price below CHF 10.00 is raised to CHF 10.00.
- [ ] AC-12b: The result is multiplied by the time-and-place factor that applies at the pickup place and the planned pickup time; without a matching rule the factor is 1.0. The offer names the factor used.
- [ ] AC-12c: Reference cases: 10 km and 5 min → CHF 25.50. 2 km and 3 min → CHF 7.50, raised to CHF 10.00. 13.172 km and 21.2 min (a recorded ride) → CHF 33.05, within CHF 0.05.
- [ ] AC-12d: The price does not depend on the car: two offers with the same distance, duration and pickup time have the same price.
- [ ] AC-12e: Tip, waiting time and the price that was charged on a recorded ride are not part of the offer. For offers backed by a recorded ride, the charged price is kept only as a check value.
- [ ] AC-13: A discount that was given on the recorded ride is not part of the offer. Promo codes are applied by the booking app (PROJ-1-PRD-3).
- [ ] AC-14: The offer contains no internal split of the price (driver earnings, service fee). Vertt is one party.
- [ ] AC-15: The price is in CHF and rounded to CHF 0.05 for the customer (demo rule, story 8).

### US-4: As an IB partner, I want the Vertt API to be documented and stable so that we can use it in the later prototypes (story 25)
**Given** I want to build on the Vertt API
**When** I read its description
**Then** I find every request and every field explained, with an example

**Acceptance Criteria:**
- [ ] AC-16: `docs/api/vertt.md` describes every request and every field, with type, meaning and one example answer, in the same style as the OJP documents.
- [ ] AC-17: Every answer of the API matches the description.
- [ ] AC-18: The API answers in JSON and carries a version; a change of a field name or meaning is a new version.
- [ ] AC-19: The demo gets its Vertt data only through this API – the trip offer middleware (PROJ-1-PRD-8) calls it – and never from the data files directly.

### US-5: As Vertt, I want the API to give away nothing about the passenger behind the rides so that we can run it openly and share it with partners (stories 21, 26)
**Given** the rides come from one real passenger
**When** anyone uses the API or looks at the repo
**Then** nothing leads back to that person

**Acceptance Criteria:**
- [ ] AC-20: No answer contains a passenger ID, a vehicle ID, an address, a street name or a postcode.
- [ ] AC-21: The route line of an offer does not begin or end at the passenger's address: the part near the home is cut off or the end is moved to the locality position.
- [ ] AC-22: Coordinates of a locality are the same for every ride and do not point to a house.
- [ ] AC-23: No answer contains the original date or clock time of a ride, nor the original ride ID.
- [ ] AC-24: The Excel export is never committed, deployed or reachable through the API. The API works from a derived set of data that passes AC-20 to AC-23.
- [ ] AC-25: The car is described by make, model and year only – no number plate.

### US-6: As Vertt, I want only our own app to reach the Vertt API so that the tariff and the offers are not open to everyone (decided 2026-10-05)
**Given** the Vertt API is running
**When** anything other than the server side of our own app calls it
**Then** the call is refused

**Acceptance Criteria:**
- [ ] AC-26: The Vertt API is called only by the server side of our app (the trip offer middleware, PROJ-1-PRD-8). The page in the customer's browser never calls it directly.
- [ ] AC-27: A call without the valid secret is refused with a clear "not allowed" answer and reveals no data.
- [ ] AC-28: The secret never appears in the page, the repo, a data link or an export.
- [ ] AC-29: Partners get the description of the API (US-4), but no access of their own in Prototype 1. Access for partners, each with a key of their own, is a later step.

## Edge Cases
- Several recorded rides exist for one route (Wettswil am Albis → Zürich HB has four, with different cars and prices): see open question.
- The same route in the other direction has no recorded ride (e.g. Schlieren → Wettswil am Albis): "not served"; the API does not mirror a ride.
- From and to are the same place: "not served".
- Both coordinates lead to the same served place: "not served".
- The coordinates are the same distance from two served places: a fixed rule decides (proposed: the first in the place list).
- The coordinates are not valid or lie outside Switzerland: a clear "invalid position" answer, different from "not served".
- An unknown place ID is asked for: a clear "unknown place" answer, different from "not served".
- The car of an offer has no CO₂ value (3 of 9 cars): the offer is still valid, CO₂ is "not available" (AC-9).
- The car model with two CO₂ values: one value is chosen by a documented rule; it is not averaged silently.
- The ride with factor 1.2 and tip (airport, a Friday night in 2022): tip and the factor of that day do not count. The offer uses the factor that applies at the planned pickup time (AC-12b).
- A very short ride: the minimum price applies (AC-12a).
- A very long ride (e.g. "Vertt only" Wettswil am Albis → Bern, about 130 km): the tariff has no long-distance discount, so the price is simply high (roughly CHF 260–270). That is the intended comparison.
- No route can be calculated for a calculated offer: fall back to AC-11d or "not served"; no price is guessed.
- The route line is missing or broken for a ride: the offer is given without a route and says so; the map then draws a straight line (PROJ-1-PRD-2 AC-25).
- A call arrives with a wrong or missing secret, or straight from a browser: refused (AC-27).
- The secret has to be replaced (e.g. it leaked): this is possible without changing the API description.

## Open Questions

**Answered from Vertt's tariff specification (2026-10-05):**
- ~~Places without data~~ → the tariff formula is known, so offers can be calculated for places without a recorded ride (AC-8a).
- ~~Price for a position, not a place~~ → the price is calculated for the exact position (AC-11d, AC-12).
- ~~Surge~~ → the historic factor of a recorded ride is not reused; the factor follows the pickup time and place (AC-12b). The demo's fixed scenario times so far lie outside all peak times → factor 1.0.
- ~~Vertt tariff formula~~ (cto-meeting T2 question 1, GitHub issue #11) → see "The Vertt tariff".

**Still open:**
- ~~Where do distance and ride time of a calculated offer come from?~~ → **Decided 2026-10-05: Valhalla** (open route service, no key). swisstopo has no car routing. Trial on the five recorded routes: [docs/api/routing.md](../../../docs/api/routing.md). Answers are stored so a repeated demo does not depend on the public server. Vertt's own route component or Google remain an option if prices should come closer to Vertt's real ones.
- **Which tariff applies outside Zurich?** The verified values are the Zurich tariff. A second Vertt leg in Bern (the mockup's Bern → Ostermundigen) would be priced with Zurich values. Acceptable for the demo? → CTO.
- **Peak-time zones.** The specification lists the factors and time windows but not the shapes of the Zurich zones (ZH1–ZH3). Needed only if a demo scenario falls into a peak time. → Vertt.
- **Price for recorded routes:** the tariff applied to the real distance and time (proposed, AC-12 – one rule for all offers), or the price that was really charged (AC-12e keeps it as a check value)? The two differ by up to 12 %. → Tim.
- **Car of a calculated offer** (AC-8b): assumed car from the provided data, or CO₂ "not available"? → Tim.
- **Rounding.** Vertt's specification keeps prices exact to CHF 0.01 and rounds to CHF 0.05 only for cash; the demo rounds every customer price to CHF 0.05 (story 8). Keep the demo rule? → Tim.
- **VAT.** Whether the tariff values include VAT, and the rate, are open in Vertt's own specification too (8.1 % assumed there). → Vertt finance.
- **Several rides on one route** are returned as several offers (AC-6a); the middleware picks. With the tariff, their prices differ only through distance and duration; what really differs is the car and its CO₂. → Tim to confirm.
- **Maximum distance** to the nearest served place (AC-11c) – only relevant for the fallback in AC-11d. Proposed: 5 km.
- ~~Who may call the API?~~ → **Decided 2026-10-05:** only our own app (US-6).
- **CO₂ unit** of the car values (g/km vs g/100km) and which value for the duplicate car model (GitHub issue #14). Not covered by the tariff specification. → Vertt.
- ~~May the tariff values be published in this public repository?~~ → **Decided 2026-10-05: yes.**
- Is "book a ride" / "cancel a ride" through the API wanted later (Prototype 2)? Not part of this PRD.

## Dependencies
- Requires: the Excel export in `data/raw/` on the machine that prepares the data (it is not in Git).
- Feeds: PROJ-1-PRD-8 (Vertt leg offers for building trips), PROJ-1-PRD-1 (places to choose from), PROJ-1-PRD-2 (Vertt legs, car, CO₂, map), PROJ-1-PRD-4 (Vertt part of the settlement), PROJ-1-PRD-5 (offer ID and data basis in the data link).
- Works with: PROJ-1-PRD-6 (stations matched by official stop ID).
- Requires for calculated offers: the route service Valhalla for distance and ride time between two positions (decided 2026-10-05, `docs/api/routing.md`).
- Supersedes: GitHub issues #8, #9, #15 (offers carry no fixed clock time, AC-7); #10 (constructed leg) and #11 (tariff formula) are answered by the tariff.

## Technical Requirements
- Read-only: the API offers places and ride offers. It takes no bookings and stores nothing about the caller.
- Reachable only from the server side of our own app, with a secret (US-6); answers in JSON.
- Because the public repo and the hosted page never contain the Excel export, the API must work without it at run time.
- An automatic check proves AC-20 to AC-23 on every answer the API can give.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: no screen of its own. Its values appear in the place selection (PROJ-1-PRD-1) and in the Vertt leg rows and the map (PROJ-1-PRD-2).
- New component candidates: none.
- Design tokens: none.
- Interaction contract: none.
- Implementation tolerance: field names are free until `docs/api/vertt.md` exists; afterwards they are fixed (AC-18).
