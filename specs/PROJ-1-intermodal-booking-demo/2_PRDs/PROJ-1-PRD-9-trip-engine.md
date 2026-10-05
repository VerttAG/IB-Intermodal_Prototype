# PROJ-1-PRD-9: Trip engine – door-to-door trips calculated live

## Status: Planned – decided by Tim 2026-10-05, to be confirmed with CTO

Every trip is **built live** from the customer's start address, destination address and departure time. There are no preset trips. A trip is a Vertt ride (or a walk) to a train station, a train with OJP, and a Vertt ride (or a walk) from the arrival station to the destination. Vertt legs are **calculated** by the Vertt API (PROJ-1-PRD-7): route from Valhalla × Vertt tariff, CO₂ from a car of the car pool. The AI model only **chooses which stations are worth trying** (PROJ-1-PRD-8); every label is decided by calculation. The engine runs inside the middleware (PROJ-1-PRD-8).

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
| Preset trips | Dropped. Every trip is calculated live for the entered addresses. |
| When calculated | **Live** for every search (needs internet and our server during the demo). |
| Recorded Vertt rides (9) | **Validation only** (PROJ-1-PRD-7 US-5). Not used in the demo. |
| Start / destination | Address fields with swisstopo suggestions, pre-filled with an example. No "use my location". |
| Time | Customer chooses **"depart at"** date and time. No "arrive by". |
| Candidate stations | Max. **3 per side**: 1 hub within **25 km** + 2 stations that make sense for the route. A station **on the way** (small detour) is preferred over a closer one that leads away from the destination. |
| Hub list | Zürich HB, Zürich Oerlikon, Zürich Flughafen, Winterthur, Bern, Olten, Aarau, Biel/Bienne, Basel SBB, Luzern, Zug, Arth-Goldau, St. Gallen, Chur, Lausanne, Genève, Fribourg, Bellinzona, Lugano, Visp, Brig (configurable). |
| Short trips | Start and destination **under 10 km** apart: no search, message "Trip not suitable for intermodal journey" (configurable). |
| AI model | **Chooses** candidate stations from a list of real stations. Receives the addresses (mock trips). Does **not** decide labels. |
| Trains per station pair | Only the **first possible train** (≥ 8 min transfer). |
| Walk instead of Vertt | At **both ends**, if the station is within **1 km** straight line (configurable). Also the minimum distance for a Vertt ride. |
| Trips without Vertt leg | Offered only if they result from the normal calculation, without extra AI or API calls. |
| Vertt tariff | Zurich values for every Vertt leg in Switzerland, **factor 1.0** – to confirm with CTO. |
| Car | Drawn from the **car pool** (Tim), once per Vertt leg. |
| Pickup | **5 min** after the chosen departure time at the start; **2 min** after the train arrival at the destination station (transfer). Both configurable. |
| Train prices | Only the **half-fare** price is fetched from OJP Fare. No travelcard = 2 × half-fare price, GA = CHF 0.00. Shown as normal prices; the data link records the source in `price_source`. |
| Response time | Results within ~5 s, with a loading state. Partner calls run in parallel. |
| Offers shown | Only the labelled trips (max. 3); other candidates are not shown. |
| Comparison cards | Both stay; not bookable, not clickable. |

## User Stories

### US-1: As a customer, I want trips for exactly my addresses and time so that the result fits my journey
**Given** I entered start, destination and "depart at" time (PROJ-1-PRD-1)
**When** I press "Search"
**Then** trips are calculated live for these inputs

**Acceptance Criteria:**
- [ ] AC-1: The engine receives start and destination (address and coordinates from swisstopo), departure date and time, and the travelcard.
- [ ] AC-2: All partner calls of a search run on the server (PROJ-1-PRD-8); the browser sends one request and gets one answer.
- [ ] AC-3: Repeating the same search gives the same result and costs no new partner calls (cache).

### US-2: As a customer, I want sensible stations to be tried so that I get a good trip even if the nearest station is not the best one
**Given** start and destination are known
**When** the engine looks for stations
**Then** it tries up to 3 stations per side, including a hub and stations that make sense for the route

**Acceptance Criteria:**
- [ ] AC-4: Per side, at most 3 candidate stations: 1 hub from the hub list if one lies within 25 km, plus 2 stations that make sense for the direction of travel.
- [ ] AC-4a: For every option the code calculates the detour (straight-line distances, no API call). Options are given to the model sorted by detour and marked "on the way" or "away from destination"; the code fallback also chooses by smallest detour, not by smallest distance.
- [ ] AC-5: The candidates are chosen by the AI model from an option list of real stations built from OJP (PROJ-1-PRD-8 US-2). The model cannot add stations.
- [ ] AC-6: If the model fails, the code chooses (PROJ-1-PRD-8 US-3). A search never fails because of the model.
- [ ] AC-7: The data link stores the candidates and whether each came from the model or the code fallback.

### US-3: As a customer, I want each candidate trip calculated with real partner data so that times, prices and CO₂ are believable
**Given** the candidate stations
**When** the engine builds the trips
**Then** every combination of start station and destination station becomes one trip

**Acceptance Criteria:**
- [ ] AC-8: For each combination (max. 9), one trip is built: first leg, train, last leg.
- [ ] AC-9: First and last leg: if the station is within 1 km (straight line) of the address, the leg is a walk (from OJP); otherwise it is a Vertt leg from the Vertt API (PROJ-1-PRD-7).
- [ ] AC-10: First Vertt leg: pickup = chosen departure time + 5 min. Last Vertt leg: pickup = train arrival + 2 min.
- [ ] AC-10a: Start and destination less than 10 km apart (straight line): no stations, no trips; the message "Trip not suitable for intermodal journey" is shown.
- [ ] AC-11: Train leg: the first train from OJP that leaves at least 8 minutes after the arrival at the station. Times, line, platform, route geometry and distance from OJP.
- [ ] AC-12: Only the **half-fare** price (2nd class) is fetched from OJP Fare (PROJ-1-PRD-6). No travelcard = 2 × half-fare price; GA = CHF 0.00. All three are shown as normal prices; the data link stores `price_source` (`ojp_fare`, `half_fare_x2`, `ga_rule`). A travelcard change needs no new search.
- [ ] AC-13: Train CO₂ as decided in CTO topic B7 (tailpipe rule 0.0 kg, or OJP value). The OJP value is always stored in the data link.
- [ ] AC-14: A trip with a missing train price, or a leg that cannot be calculated, is not offered.
- [ ] AC-15: If both ends are walks, the trip is a train-only trip. It is offered like any other trip, because it costs no extra calls.

### US-4: As a customer, I want to see the fastest, cheapest and greenest trip so that I can choose by what matters to me (story 27)
**Given** the candidate trips are calculated
**When** the connection list is shown
**Then** I see up to 3 labelled, bookable trips and the two comparison cards

**Acceptance Criteria:**
- [ ] AC-16: Totals per trip: arrival time, duration (door to door), price (sum of rounded leg prices), CO₂.
- [ ] AC-17: "Fastest" = earliest arrival; "Cheapest" = lowest total price; "Greenest" = lowest total CO₂. Labels are decided by calculation only.
- [ ] AC-18: A trip that wins several labels is shown once with all its labels. Other candidate trips are not shown.
- [ ] AC-19: Ties: earlier arrival first, then lower price.
- [ ] AC-20: Comparison "Vertt only": one Vertt API offer for the whole route. Comparison "Public transport only": OJP door to door. Both show times, price and CO₂.
- [ ] AC-21: Changing the travelcard recalculates prices and labels from the stored half-fare price, without new partner calls (AC-12).
- [ ] AC-22: Partner calls of a search run in parallel; the list appears within ~5 s, with a loading state until then.

### US-5: As the CTO, I want the calculator checked against real rides so that I can trust the Vertt prices
- See PROJ-1-PRD-7 US-5 (validation with the 9 recorded rides).

## Edge Cases
- No hub within 25 km: 3 stations with the smallest detour instead.
- Start and destination under 10 km apart: message "Trip not suitable for intermodal journey" (AC-10a).
- OJP Fare limit (50 calls/min): about 4 new searches per minute; above that a clear message "Too many searches, please wait a moment".
- Start or destination is itself a station: walk leg of 0 minutes, i.e. no first/last leg.
- OJP finds no train for a station pair at the chosen time (night): that combination is skipped.
- All combinations fail: clear message "no trip found for this time".
- OJP or OJP Fare limit reached (50 calls/min): cached answers are used; otherwise a clear message, never made-up data.
- Valhalla public server unreachable: cached answers; otherwise the Vertt leg cannot be calculated → trip not offered.
- GA: all train prices CHF 0.00 → "Cheapest" decided by the Vertt legs.

## Open Questions
- **Train CO₂ on screen** (CTO topic B7): 0.0 kg (tailpipe) or the OJP value?
- Answered 2026-10-05 (Tim): walk threshold 1 km · waiting time 5 / 2 min · hub list + 25 km + detour rule · short trips under 10 km → message · ~5 s response · half-fare only, × 2 for no travelcard.

## Dependencies
- Requires: swisstopo address search (`docs/api/geocoding.md`), Valhalla (`docs/api/routing.md`), OJP 2.0 and OJP Fare (`docs/api/ojp20.md`, `docs/api/ojpfare.md`), Vertt API (PROJ-1-PRD-7), car pool (`config/car_pool.yaml`), AI station choice (PROJ-1-PRD-8).
- Feeds: PROJ-1-PRD-2 (connection list), PROJ-1-PRD-3 (overview), PROJ-1-PRD-5 (data link: candidates, sources, assumptions).
- Needs a server (keys for OJP, OJP Fare, Vertt API, OpenRouter must not reach the browser) → CTO topic T1 / hosting; password gate (`mockup/middleware.js`).

## Technical Requirements
- All keys stay on the server; the browser calls one entrance of our own (PROJ-1-PRD-8 AC-4 to AC-6).
- API calls per search are capped: max. 3 stations per side, first train only. All answers are cached so a repeated search costs no calls.
- All money, time and CO₂ calculations happen in code, never in the model.
- Every assumption (tariff region, factor 1.0, waiting time, pool car, walk threshold) is configurable and stored with each trip in the data link.
