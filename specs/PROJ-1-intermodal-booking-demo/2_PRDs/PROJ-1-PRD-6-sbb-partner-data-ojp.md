# PROJ-1-PRD-6: SBB partner data from OJP and OJP Fare

## Status: Planned

Covers everything the demo needs from the SBB side: stations, train connections and train prices. They come from the two official interfaces, OJP 2.0 (journey planner) and OJP Fare (prices). Source: [docs/user-stories.md](../../../docs/user-stories.md) stories 22, 23 (proposed, v1.1); findings in [docs/api/ojp20.md](../../../docs/api/ojp20.md) and [docs/api/ojpfare.md](../../../docs/api/ojpfare.md).

This PRD says **what** the demo gets from SBB. Whether the answers are fetched while the user clicks or prepared in advance is decided in the architecture step.

## User Stories

### US-1: As SBB, I want the stations in the demo to be the official ones so that train connections can be searched for them (story 22)
**Given** a station name used in the demo
**When** it is looked up
**Then** the official stop with its ID and coordinates is found
**And** it is the train station, not a bus or tram stop with a similar name

**Acceptance Criteria:**
- [ ] AC-1: Every station used in the demo is resolved through OJP 2.0 to its official stop ID (SLOID), name and coordinates.
- [ ] AC-2: Where a name returns several stops (e.g. "Zürich HB" also returns tram stops), the rail stop is used.
- [ ] AC-3: A station that cannot be resolved is not offered in the demo.

### US-2: As SBB, I want the train legs of the demo to come from the official journey planner so that times, lines and platforms are real (story 22)
**Given** a start station, a destination station and a departure time
**When** the train part of a journey is planned
**Then** the legs come from OJP 2.0 with their real times and lines

**Acceptance Criteria:**
- [ ] AC-4: Each train leg has from, to, departure, arrival, duration and line (e.g. IC 8, S11), taken from the OJP 2.0 answer.
- [ ] AC-5: Times are shown in Swiss local time (OJP answers in UTC).
- [ ] AC-6: After the first leg (Vertt ride or walk), only trains departing at least 8 minutes after the arrival at the station are considered, and only the **first** such train is used per station pair (decided 2026-10-05, PROJ-1-PRD-9). Variety comes from the candidate stations.
- [ ] AC-7: A train part with a change of trains is kept as several train legs with the transfer time between them.
- [ ] AC-8: The route of each train leg on the map follows the railway line, using the geometry from OJP.
- [ ] AC-9: The distance of each train leg comes from OJP.
- [ ] AC-10 *(Could)*: The platform of each train leg is taken from OJP when it is present.
- [ ] AC-11: The demo date lies within the timetable period OJP covers; journeys are not planned for past dates.

### US-3: As a customer, I want the public-transport-only alternative to be a real connection so that the comparison is fair (stories 6, 22)
**Given** a start and a destination that are not both stations
**When** the comparison connections are built
**Then** the public-transport-only connection comes from OJP 2.0, door to door

**Acceptance Criteria:**
- [ ] AC-12: The public-transport-only connection is the OJP 2.0 answer for the same start, destination and departure time, including bus, tram and walking parts.
- [ ] AC-13: If OJP finds no such connection, the card is left out or a note explains why (PROJ-1-PRD-2 AC-5).

### US-4: As SBB, I want the train price in the demo to come from the official price interface so that the customer and the partners see a real price (story 23)
**Given** a train connection from OJP 2.0 and a travelcard
**When** its price is determined
**Then** the price comes from OJP Fare for 1 adult, 2nd class

**Acceptance Criteria:**
- [ ] AC-14: For "no travelcard" and "half-fare", the train price is the price OJP Fare returns for exactly this connection.
- [ ] AC-15: Only 2nd-class prices are used, although OJP Fare also returns 1st class.
- [ ] AC-16: A half-fare price is only accepted if the answer confirms the half-fare card was applied; otherwise the price counts as not available.
- [ ] AC-17: For GA the train price is CHF 0.00 by the demo's own rule, because OJP Fare does not recognise GA.
- [ ] AC-18: If OJP Fare offers several 2nd-class products, one fixed rule picks the product, and the product name is kept with the price.
- [ ] AC-19: A price covers the train legs OJP Fare names; a price for several legs is not counted twice.
- [ ] AC-20: With every price, the product name, product ID, price without VAT and VAT rate are kept for the data link (PROJ-1-PRD-5).
- [ ] AC-21: The price is marked with its source, "OJP Fare (beta)".

### US-5: As a customer, I want the price I saw to be the price I pay so that a changing saver price does not surprise me (story 23)
**Given** I see a train price in the overview
**When** I pay
**Then** the booking holds exactly that price
**And** it does not change afterwards

**Acceptance Criteria:**
- [ ] AC-22: The train price shown in the overview is the price charged and stored in the booking.
- [ ] AC-23: The stored price of a booking never changes, also not when OJP Fare returns a different price later (settlement and cancellation use the stored price).

### US-6: As a demo presenter, I want the demo to stay honest and usable when the SBB interfaces fail so that I never show made-up numbers as real (stories 22, 23)
**Given** OJP 2.0 or OJP Fare does not answer, or answers without the needed value
**When** the journey is planned
**Then** the missing value is shown as not available or comes from a stored earlier answer, marked as such

**Acceptance Criteria:**
- [ ] AC-24: A missing price is shown as "not available", never as CHF 0.00.
- [ ] AC-25: A connection without a train price cannot be booked.
- [ ] AC-26: A value taken from a stored earlier answer is marked as such in its data source.
- [ ] AC-27: No value is invented when an interface fails.

## Edge Cases
- The train part runs over midnight or over a daylight-saving change: local times and durations stay correct.
- No train within a sensible wait after the Vertt arrival (late evening): the journey is not offered, or the long wait is marked (PROJ-1-PRD-2 AC-12).
- OJP Fare returns no product for a connection: "not available" (AC-24), not bookable (AC-25).
- OJP Fare returns only a saver ticket in 2nd class when no travelcard is set (seen in the test): see open question.
- The same connection gets a different price later the same day (saver prices follow demand): bookings already made keep their price (AC-23).
- Values come back with stray spaces or without a time zone (seen in the test): they are read correctly or not used.
- The daily or per-minute limit of the interfaces is reached during a demo: behaviour as in US-6.
- The demo date is after the end of the current timetable period: the route is not offered.

## Open Questions
- **Saver or normal ticket?** For "no travelcard", OJP Fare returned only a saver ticket (Sparbillett, bound to one train, price changes) in 2nd class: CHF 38.80 for Zürich HB → Bern. Proposed rule for AC-18: cheapest 2nd-class product. Is a saver price acceptable as "the" SBB price, also for the settlement? → Tim / CTO (cto-meeting B8).
- **Train CO₂:** OJP delivers a factor (0.007 kg per person-km → 0.8 kg for Zürich–Bern), while the agreed rule is "tailpipe only → trains 0.0 kg". Keep 0.0 on screen and store the OJP value in the data link only? → CTO (B7).
- ~~Live or prepared in advance?~~ → **Decided 2026-10-05: live** for every search (PROJ-1-PRD-9). The demo needs internet access to SBB during the presentation; answers are cached.
- ~~SBB → Vertt journeys: search by arrival time?~~ → **Decided:** no "arrive by"; the last Vertt pickup follows the train arrival + waiting time (PROJ-1-PRD-9 AC-10).
- Both prices ("no travelcard" and "half-fare") are fetched in every search (PROJ-1-PRD-9 AC-12) – twice the OJP Fare calls. OK within the limit of 50 calls/min? → spike.

## Dependencies
- Feeds: PROJ-1-PRD-8 (train legs and prices as leg offers), PROJ-1-PRD-2 (train legs, prices, map), PROJ-1-PRD-4 (train part of the settlement), PROJ-1-PRD-5 (data sources and price details in the data link).
- Works with: PROJ-1-PRD-7 (the train is chosen relative to the Vertt leg, AC-6).
- External: access keys for OJP 2.0 and OJP Fare (separate keys; both exist). OJP Fare is a beta service.

## Technical Requirements
- The access keys never appear in the page, the repo, a data link or an export.
- The limits of both interfaces are respected: 20,000 calls per day and 50 per minute each. One price needs two calls (connection, then price).
- Answers are stored so that a repeated demo does not ask again for the same thing.
- Every SBB value carries its data source: "OJP 2.0", "OJP Fare (beta)", "demo rule" (GA) or "stored answer".

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: no screen of its own. The values appear in the connection cards and leg rows of PROJ-1-PRD-2 and in the overview and receipt of PROJ-1-PRD-3.
- New component candidates: none here ("not available" value is listed in PROJ-1-PRD-2).
- Design tokens: none.
- Interaction contract: none.
- Implementation tolerance: the interface quirks listed in `docs/api/ojp20.md` section 5 and `docs/api/ojpfare.md` section 6 are known facts to respect, not suggestions.
