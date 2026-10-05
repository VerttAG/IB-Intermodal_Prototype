# PROJ-1-PRD-2: Connections and leg details

## Status: Planned

Covers the connection list and the connection details of step 1 (the most important part of the demo). Source: [docs/PRD.md](../../../docs/PRD.md) section 4, [docs/user-stories.md](../../../docs/user-stories.md) stories 6–11. Story numbers are given in brackets.

## User Stories

### US-1: As a customer, I want to see several ways to make my journey side by side so that I can choose the one that suits me (story 6)
**Given** start, destination and travelcard are set
**When** I look at the connection list
**Then** I see up to three connections with times, price and CO₂
**And** only the Vertt + SBB connection can be booked

**Acceptance Criteria:**
- [ ] AC-1: The list shows, in this order: the Vertt + SBB trip offers – up to three, labelled "Fastest", "Cheapest" and "Greenest" (PROJ-1-PRD-8) –, then Vertt only, then public transport only.
- [ ] AC-2: Each card shows departure, arrival, duration, number of transfers, transport mode icons, total price and total CO₂.
- [ ] AC-3: Only the Vertt + SBB trip offers can be booked. The other two are marked "for comparison" and have no way to continue to booking.
- [ ] AC-4: Tapping a Vertt + SBB card opens the details of that trip offer (US-2).
- [ ] AC-5: If a connection type does not exist for a route, the card is left out or a note explains why. This includes a "Vertt only" connection for which Vertt has no ride offer (PROJ-1-PRD-7) and a public-transport connection OJP does not find (PROJ-1-PRD-6).

### US-2: As a customer, I want to see every leg in detail so that I know what happens and where I need to be (story 7)
**Given** I opened the details of a connection
**When** I look at the legs
**Then** each leg shows who carries me, from where to where and when
**And** I see how much time I have at each transfer

**Acceptance Criteria:**
- [ ] AC-6: Each leg shows carrier, mode icon, from → to, departure, arrival and duration.
- [ ] AC-7: Train legs show the line (e.g. S11, IC 8), as delivered by OJP (PROJ-1-PRD-6).
- [ ] AC-8: Vertt legs show the car category. Prototype 1 has one category, "Vertt".
- [ ] AC-9: The car of a Vertt leg comes from the Vertt ride offer for this leg (PROJ-1-PRD-7). Each trip offer has its own ride and car; once the customer has chosen an offer, its car stays the same until the run ends. *(Changes story 7, which drew one car from a separate pool – see open questions.)*
- [ ] AC-10: Between two legs a transfer row shows the minutes available.
- [ ] AC-11: From the details I can continue to the next step or go back to the connection list.
- [ ] AC-12 *(Could)*: A transfer shorter than 8 min is marked "tight", one longer than 15 min "long wait".
- [ ] AC-13 *(Could)*: Train legs show the platform if it is available.

### US-3: As a customer, I want to see what each leg costs and what I pay in total so that I understand the price and can compare (story 8)
**Given** a connection is shown
**When** I look at the prices
**Then** I see a price per leg and a clear total
**And** I see when my travelcard changed the train price

**Acceptance Criteria:**
- [ ] AC-14: Each leg shows its price in CHF with two decimals, rounded to CHF 0.05. Vertt prices come from the Vertt ride offer (PROJ-1-PRD-7), train prices from OJP Fare (PROJ-1-PRD-6).
- [ ] AC-15: The total equals the sum of the rounded leg prices. There are no other amounts.
- [ ] AC-16: With half-fare the train leg carries the hint "half-fare price". With GA it shows CHF 0.00 and "covered by GA".
- [ ] AC-17: The two comparison connections also show a total price, and it follows the travelcard where public transport is included.

### US-4: As a customer, I want to see how much CO₂ each leg and the whole journey cause so that I can choose a climate-friendly connection (story 9)
**Given** a connection is shown
**When** I look at the CO₂ values
**Then** I see kg CO₂ per leg and in total, per person

**Acceptance Criteria:**
- [ ] AC-18: CO₂ is shown in kg with one decimal, per person, per leg and as a total.
- [ ] AC-19: Only tailpipe emissions count: electric trains and electric cars show 0.0 kg.
- [ ] AC-20: The CO₂ of a Vertt leg is the distance times the CO₂ factor of the car, both from the Vertt ride offer.
- [ ] AC-21: A value that cannot be calculated shows "not available", never 0.
- [ ] AC-22: No comparison text is shown (no "saves X kg").

### US-5: As a customer, I want to see my whole journey on a map so that I understand where the car takes me, where I change and where the train goes (story 10)
**Given** I opened the details of the bookable connection
**When** I look at the map
**Then** I see all legs coloured by carrier, with start, transfer points and destination marked

**Acceptance Criteria:**
- [ ] AC-23: A map is shown for the bookable connection only, in the connection details and in the overview (PROJ-1-PRD-3).
- [ ] AC-24: Each leg is coloured by carrier and a legend explains the colours.
- [ ] AC-25: Vertt legs follow the streets and train legs follow the railway line. If no geometry is available the leg is a straight line and is marked as such.
- [ ] AC-26: Markers show start, each transfer point and destination. They show the known place, not an address entered by the customer.
- [ ] AC-27: The map opens zoomed so the whole journey is visible. Legs are not highlighted on interaction.

### US-6: As a customer, I want to see why a connection is recommended so that I understand the benefit of booking Vertt and SBB together (story 11, Should)
**Given** the connection list is shown
**When** I look at the Vertt + SBB connection
**Then** it is labelled as recommended, with the reason

**Acceptance Criteria:**
- [ ] AC-28: The Vertt + SBB trip offers carry the fixed text "Door to door with one booking". The "Recommended" tag is replaced by the labels "Fastest", "Cheapest" and "Greenest" (PROJ-1-PRD-8) – see open questions there.

## Edge Cases
- The car is electric: Vertt legs show 0.0 kg (a real value), not "not available". The provided Vertt data contains no electric car.
- The car has no CO₂ factor – true for 3 of the 9 cars in the provided data: the Vertt leg shows "not available" (AC-21). See open question for the total.
- A train price is "not available" (PROJ-1-PRD-6 AC-24): the connection shows no total and cannot be booked.
- GA: the train leg is CHF 0.00, so the total is the Vertt part only.
- The Vertt-only comparison has its own ride offer and therefore its own car; without an offer it is left out (AC-5).
- A journey has one Vertt leg (Vertt → SBB or SBB → Vertt) or two (Vertt → SBB → Vertt): list, details and map work for all three shapes.
- The map tiles cannot be loaded (no internet in the meeting room): legs, prices and CO₂ stay readable and booking still works.
- A transfer has 0 or negative minutes in the prepared data: this is a data error and must not be shown as a bookable connection.

## Open Questions
- **Car from the ride offer instead of a pool (AC-9).** With the Vertt API, each recorded ride brings its own car. The agreed story 7 draws one car from a pool for the whole run. With the trip offer middleware (PROJ-1-PRD-8) nothing is drawn at random any more: each trip offer is built from one recorded ride and brings its car. → Tim.
- **Journey shapes.** With recorded rides alone, only Vertt → SBB and SBB → Vertt are possible. With the Vertt tariff (PROJ-1-PRD-7) a second Vertt leg and the "Vertt only" comparison can be calculated – once a route service is chosen. → CTO.
- **Do the comparison cards open details?** Story 6 says tapping a card opens the details, story 10 says the map exists only for the bookable connection, and in the lite mockup the comparison cards do nothing. AC-4 covers only the bookable card until this is decided. → Tim.
- **Total CO₂ when one leg is "not available":** show "not available" for the total, or the sum of the known legs with a note? → Tim.
- Should estimated or placeholder values be marked on screen (cto-meeting B1)?
- CO₂ method: stay with tailpipe only (cto-meeting B7)? OJP delivers a train CO₂ value that is not 0 (PROJ-1-PRD-6).

## Dependencies
- Requires: PROJ-1-PRD-8 (the trip offers and their labels – the only source of the list), PROJ-1-PRD-1 (start, destination, travelcard, app), PROJ-1-PRD-6 (train legs, train prices, public-transport alternative, railway geometry), PROJ-1-PRD-7 (Vertt legs, Vertt prices, car, street geometry).
- Feeds: PROJ-1-PRD-3 (legs, prices, CO₂ and map reused in the overview), PROJ-1-PRD-5 (legs, car and data source of each value in the data link).
- Open decisions: GitHub issue #14 (CO₂ unit of the car data). The sources of Vertt and SBB data (cto-meeting T2, B8) are now set by PROJ-1-PRD-7 and PROJ-1-PRD-6.

## Technical Requirements
- Every number on screen can be traced to its source (PRD definition of done).
- Carriers are never told apart by colour alone: leg rows name the carrier and the map has a legend.
- The list and the details are usable without the map.
- The car pool holds make, model, year and CO₂ factor only – no number plates.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: connection cards on screen "plan" and screen "detail" of the lite mockup, [mockup/index.html](../../../mockup/index.html), live at https://ib-intermodal-prototype.vercel.app.
- New component candidates: transfer warning ("tight" / "long wait"), "not available" value, marker for straight-line legs. None of these are in the mockup.
- Design tokens: none defined yet; the mockup uses one colour each for Vertt, SBB and bus.
- Interaction contract: card opens details, back to list, continue, map fitted to the journey.
- Implementation tolerance: layout and wording may change; order of the cards, the "for comparison" marking and the rounding rules may not.
