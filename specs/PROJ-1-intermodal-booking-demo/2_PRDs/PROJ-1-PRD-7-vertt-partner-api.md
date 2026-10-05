# PROJ-1-PRD-7: Vertt partner API

## Status: Planned

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
| The export's rates (1.80 per km, 0.30 per min) do not reproduce the prices | Prices are taken from the rides, not calculated |

Routes with recorded rides:

| From | To | Rides | Price range (CHF) |
|---|---|---|---|
| Wettswil am Albis | Zürich HB | 4 | 33.65 – 34.65 |
| Zürich HB | Wettswil am Albis | 2 | 31.00 – 31.30 |
| Wettswil am Albis | Schlieren (station) | 1 | 23.90 |
| Zürich Enge (station) | Wettswil am Albis | 1 | 30.70 |
| Zürich Flughafen | Wettswil am Albis | 1 | 66.40 (with surge) |

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
- [ ] AC-7: The offer does not contain a clock time; the app places the ride in the journey (before or after the train).
- [ ] AC-8: The offer says how its values came about: recorded, or constructed.
- [ ] AC-9: If the CO₂ factor of the car is unknown, the offer says so; it does not contain 0.
- [ ] AC-10: For a combination Vertt does not serve, the API answers clearly "not served"; it never returns an estimate without marking it.
- [ ] AC-11: Asking twice with the same offer ID returns the same offer.

### US-3: As Vertt, I want the price in an offer to follow one clear rule so that partners and the settlement work with the right amount (story 24)
**Given** a recorded ride behind an offer
**When** the offer price is set
**Then** it is the full ride price, without tip and without a past discount

**Acceptance Criteria:**
- [ ] AC-12: The offer price is the ride's gross price ("Ride Price"): before any past discount and without tip.
- [ ] AC-13: A discount that was given on the recorded ride is not part of the offer. Promo codes are applied by the booking app (PROJ-1-PRD-3).
- [ ] AC-14: The offer contains no internal split of the price (driver earnings, service fee). Vertt is one party.
- [ ] AC-15: The price is in CHF including VAT and is a multiple of CHF 0.05.

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

## Edge Cases
- Several recorded rides exist for one route (Wettswil am Albis → Zürich HB has four, with different cars and prices): see open question.
- The same route in the other direction has no recorded ride (e.g. Schlieren → Wettswil am Albis): "not served"; the API does not mirror a ride.
- From and to are the same place: "not served".
- An unknown place ID is asked for: a clear "unknown place" answer, different from "not served".
- The car of an offer has no CO₂ value (3 of 9 cars): the offer is still valid, CO₂ is "not available" (AC-9).
- The car model with two CO₂ values: one value is chosen by a documented rule; it is not averaged silently.
- The ride with surge and tip (airport): the tip never counts (AC-12); see open question for the surge.
- The route line is missing or broken for a ride: the offer is given without a route and says so; the map then draws a straight line (PROJ-1-PRD-2 AC-25).
- A partner asks very often: the API stays available for the demo.

## Open Questions
- **Places without data.** The provided rides cover only Wettswil am Albis ↔ four stations. Not possible from this data:
  - a second Vertt leg at the destination (the mockup's Bern → Ostermundigen), so no Vertt → SBB → Vertt journey;
  - the "Vertt only" comparison for a long route (e.g. Wettswil am Albis → Bern).
  Options: (a) leave them out of Prototype 1, (b) allow **constructed** offers, clearly marked – this needs the Vertt tariff formula (cto-meeting T2, question 1) or more rides from Vertt. → Tim / CTO.
- **Several rides on one route** are returned as several offers (AC-6a); the middleware picks. This replaces "the car is drawn from a pool" (story 7) with real ride + car pairs. → Tim to confirm.
- **Surge:** keep the airport ride with its surge price (CHF 66.40), remove the surge, or leave the route out? → CTO.
- **Who may call the API?** Open to everyone like the public repo, or only with a key? It shows real Vertt ride prices. → CTO.
- **CO₂ unit** of the car values (g/km vs g/100km) and which value for the duplicate car model (GitHub issue #14). → Vertt.
- Is "book a ride" / "cancel a ride" through the API wanted later (Prototype 2)? Not part of this PRD.

## Dependencies
- Requires: the Excel export in `data/raw/` on the machine that prepares the data (it is not in Git).
- Feeds: PROJ-1-PRD-8 (Vertt leg offers for building trips), PROJ-1-PRD-1 (places to choose from), PROJ-1-PRD-2 (Vertt legs, car, CO₂, map), PROJ-1-PRD-4 (Vertt part of the settlement), PROJ-1-PRD-5 (offer ID and data basis in the data link).
- Works with: PROJ-1-PRD-6 (stations matched by official stop ID).
- Supersedes: GitHub issues #8, #9, #15 (offers carry no clock time, AC-7); #10 and #11 move to the first open question.

## Technical Requirements
- Read-only: the API offers places and ride offers. It takes no bookings and stores nothing about the caller.
- Reachable from the hosted demo and by partners with a normal HTTP request; answers in JSON.
- Because the public repo and the hosted page never contain the Excel export, the API must work without it at run time.
- An automatic check proves AC-20 to AC-23 on every answer the API can give.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: no screen of its own. Its values appear in the place selection (PROJ-1-PRD-1) and in the Vertt leg rows and the map (PROJ-1-PRD-2).
- New component candidates: none.
- Design tokens: none.
- Interaction contract: none.
- Implementation tolerance: field names are free until `docs/api/vertt.md` exists; afterwards they are fixed (AC-18).
