# PROJ-1-PRD-8: Trip engine and AI station choice

## Status: Planned – decided by Tim 2026-10-05

A service of our own on the server (**Vercel**), between the partner interfaces and the booking app. For every search it **builds door-to-door trips live** from the customer's start address, destination address and departure time: a Vertt ride (or a walk) to a station, a train (OJP), and a Vertt ride (or a walk) to the destination. It gets the legs from SBB (PROJ-1-PRD-6) and Vertt (PROJ-1-PRD-7), calculates totals and labels, and serves the result to the booking app. An **AI model chooses which stations are worth trying**; every label is decided by calculation. Stories 27, 28, 29 (see [docs/PRD.md](../../../docs/PRD.md) section 5).

## How a search works

```
1. Customer: start address, destination address, "depart at" date + time, travelcard → "Search"
2. swisstopo: addresses → coordinates. Under 10 km apart → "Trip not suitable for intermodal journey", stop.
3. Candidate stations, separately for start and destination – max. 3 per side:
     code:  option list from OJP – ~10 nearest stations with train service + hubs (fixed list) within 25 km,
            each with its detour = (start→station) + (station→destination) − (start→destination)
     AI:    Jev chooses 1 hub + 2 stations that make sense for the route (on the way, small detour)
     code:  fills up if the model fails (hub with smallest detour, then stations with smallest detour)
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

## Decisions (Tim, 2026-10-05)

| Topic | Decision |
|---|---|
| Preset trips | None. Every trip is calculated **live** for the entered addresses (needs internet and our server during the demo). |
| Recorded Vertt rides (9) | **Validation only** (PROJ-1-PRD-7 US-5). Not used in the demo. |
| Start / destination | Address fields with swisstopo suggestions, **empty** in the first version; "Search" button. No "use my location". |
| Time | Customer chooses **"depart at"** date and time. No "arrive by". |
| Short trips | Start and destination **under 10 km** apart: no search, message "Trip not suitable for intermodal journey". |
| Candidate stations | Max. **3 per side**: 1 hub within **25 km** + 2 stations that make sense for the route. A station **on the way** (small detour) is preferred over a closer one that leads away from the destination. |
| Hub list | Zürich HB, Zürich Oerlikon, Zürich Flughafen, Winterthur, Bern, Olten, Aarau, Biel/Bienne, Basel SBB, Luzern, Zug, Arth-Goldau, St. Gallen, Chur, Lausanne, Genève, Fribourg, Bellinzona, Lugano, Visp, Brig. |
| AI model | **Jev 1.13** (TypeSafe) via **OpenRouter**. **Chooses** candidate stations from a list of real stations. Receives the addresses – needed for the choice and fine, all trips are mock trips. Does **not** decide labels. |
| Trains per station pair | Only the **first possible train** (≥ 8 min transfer). |
| Walk instead of Vertt | At **both ends**, if the station is within **1 km** straight line. Also the minimum distance for a Vertt ride. |
| Trips without Vertt leg | Offered only if they result from the normal calculation, without extra calls. |
| Vertt tariff | **Same tariff everywhere** in Switzerland, factor 1.0. |
| Car | Drawn from the **car pool** (Tim, `config/car_pool.yaml`), once per Vertt leg. |
| Pickup | **5 min** after the chosen time at the start; **2 min** after the train arrival at the destination station. |
| Train price | Only the **half-fare** price from OJP Fare; no travelcard = 2 × half-fare, GA = CHF 0.00. Shown as normal prices. |
| Train CO₂ | The **OJP value** (EmissionCO₂ per person-km × distance). |
| Response time | Results within ~5 s, with a loading state. Partner calls run in parallel. |
| Offers shown | Only the labelled trips (max. 3) + the two comparison cards (not bookable, not clickable). |
| Hosting | **Vercel**, behind the password gate (`mockup/middleware.js`, `DEMO_PASSWORD`). |

All values (thresholds, waiting times, hub list, radius, AI limits) are configurable.

## What we know about the model

Checked on 2026-10-05 against OpenRouter and the TypeSafe documentation.

| Fact | Consequence |
|---|---|
| Jev is a **decision model**: it picks one of the options it is given, with a probability. It does not write text and cannot invent options. | The engine builds a list of real stations (from OJP); the model only **chooses** among them. |
| Its documentation says it is **not reliable with numbers, dates and times** ("keep the arithmetic in code"). | All calculations stay in code (including the detour). Choosing sensible stations is a judgement, which suits the model. |
| Its answer can depend on the **order** of the options. | The choice must be the same when the stations are listed in another order (AC-25). |
| Extra, unrelated content lowers its accuracy; limit 32,000 tokens per request. | Only the values needed for the choice are sent. |
| Price: USD 0.042 per million input tokens, output free. | Cost is negligible for a demo. |
| OpenRouter serves it on its own "decisions" endpoint (marked alpha). | It can change → the code fallback (AC-26) matters. Risk accepted 2026-10-05. |

Earlier trial (2026-10-05, a labels task): right in 210 of 210 decisions on calculated totals; median answer 0.3 s, slowest 1.6 s; all wrong answers in a harder variant had a certainty of 0.76 or lower. The **station task** is tried in a spike before building (open questions).

## User Stories

### US-1: As a partner app, I want one service that returns complete trip offers so that I don't have to combine the partners' leg offers myself (story 28)
**Given** start and destination address, departure time and travelcard
**When** the booking app presses "Search"
**Then** it gets up to three labelled trips and the two comparison cards in one answer

**Acceptance Criteria:**
- [ ] AC-1: The browser sends one request and gets one answer: labelled trips and comparison cards, each with all legs, totals and labels.
- [ ] AC-2: Vertt legs come only from the Vertt API (PROJ-1-PRD-7); train legs, walk legs and prices only from OJP and OJP Fare (PROJ-1-PRD-6). The engine holds no leg data of its own.
- [ ] AC-3: The answer is JSON and documented in `docs/api/trip-offers.md`.
- [ ] AC-4: Not a public service (decided 2026-10-05): one entrance for our own frontend, behind the password gate; requests from other websites are refused and the number of searches per visitor is limited.
- [ ] AC-5: Vertt API, OJP, OJP Fare, Valhalla and the model are called from the server only, with secrets the browser never sees.
- [ ] AC-6: Repeating the same search gives the same result and costs no new partner calls (cache).

### US-2: As a customer, I want sensible stations to be tried so that I get a good trip even if the nearest station is not the best one (story 29)
**Given** start and destination are known
**When** the engine looks for stations
**Then** it builds a list of real stations and the AI model chooses which ones to try

**Acceptance Criteria:**
- [ ] AC-7: Per side, the code builds an option list from OJP: the ~10 nearest stations with train service and the hubs from the hub list within 25 km. Each option has name, stop ID, distance to the address, whether it is a hub, and its **detour** (straight-line distances, calculated in code).
- [ ] AC-8: Options are given to the model sorted by detour and marked "on the way" or "away from destination".
- [ ] AC-9: The model chooses per side **1 hub** (if one is in the list) and **2 stations that make sense for the route**.
- [ ] AC-10: The model receives the start and destination address, the option lists and the direction of travel – nothing about login, payment or travelcard.
- [ ] AC-11: Only stations from the option list are accepted; anything else in the answer is ignored.

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

### US-5: As a demo presenter, I want the search to work even when the model fails so that a demo never breaks because of the AI (story 29)
**Given** the model is asked for stations
**When** it is not sure, too slow or unreachable
**Then** the code chooses the stations instead

**Acceptance Criteria:**
- [ ] AC-25: The same addresses and options lead to the same choice, also in a different order. Choices are cached during a demo.
- [ ] AC-26: If the model is below the certainty threshold (**0.8**), does not answer within **2 s**, or cannot be reached, the code chooses: the hub with the smallest detour, then the stations with the smallest detour. The customer still gets trips.
- [ ] AC-27: If the model chooses fewer valid stations than needed, the code fills up the same way.
- [ ] AC-28: The server log records per search the candidates and whether each came from the model or the code, with the model's name, version and certainty; how often the model was used, unsure or unavailable can be read out after a demo. Not part of the data link.

## Edge Cases
- No hub within 25 km: 3 stations with the smallest detour instead.
- Fewer than 3 stations with train service near an address: fewer candidates; the engine works with what there is.
- Start or destination is itself a station: it is always a candidate; first/last leg is a walk of 0 minutes.
- The model picks the same station for both sides: that combination is skipped.
- The model answers something unusable: treated like "no answer" (AC-26).
- OJP finds no train for a station pair at the chosen time (night): that combination is skipped. All fail → "no trip found for this time".
- OJP Fare limit (50 calls/min): about 4 new searches per minute; cached searches are free; above that "Too many searches, please wait a moment" – never made-up data.
- Valhalla public server unreachable: cached answers; otherwise the Vertt leg cannot be calculated → trip not offered.
- OpenRouter's limit or credit is used up: AC-26 applies; no error page.
- GA: all train prices CHF 0.00 → "Cheapest" decided by the Vertt legs.

## Open Questions
- **Spike first (decided 2026-10-05):** before building, try the station task on 5–10 example journeys (e.g. Wettswil am Albis → Bern, Winterthur → Luzern, a Basel suburb → Zürich Flughafen). Code builds the option lists, Jev chooses, Tim judges. Uses Aleksandar's key (`OPENROUTER_API_KEY` in `.env`).
- Confirm in the spike: threshold 0.8 and 2 s; whether the model needs more context per station (e.g. trains per hour – costs OJP calls).
- **Example address pair** to pre-fill later (e.g. Wettswil am Albis → Ostermundigen), once the engine has been tried.

## Dependencies
- Requires: swisstopo ([docs/api/geocoding.md](../../../docs/api/geocoding.md)), Valhalla ([docs/api/routing.md](../../../docs/api/routing.md)), OJP 2.0 and OJP Fare ([ojp20.md](../../../docs/api/ojp20.md), [ojpfare.md](../../../docs/api/ojpfare.md)), Vertt API (PROJ-1-PRD-7), car pool, OpenRouter (Aleksandar's key), Vercel.
- Feeds: PROJ-1-PRD-2 (connection list), PROJ-1-PRD-3 (overview), PROJ-1-PRD-5 (amounts and CO₂ per operator for the data link).

## Technical Requirements
- Runs on Vercel (server functions); the OpenRouter, OJP, OJP Fare and Vertt API keys are Vercel environment variables and never appear in the page, the repo, a data link or an export.
- API calls per search are capped: max. 3 stations per side, first train only, half-fare price only. All answers are cached.
- All money, time, distance and CO₂ calculations happen in code, never in the model.
- The model version is fixed (Jev 1.13), not "latest".

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- No screen of its own: its result fills the connection list (PROJ-1-PRD-2). Optional small note on a trip: "stations chosen by AI".
- Implementation tolerance: how the option list is built may change; the rule that the model only chooses among real stations (AC-11) may not.
