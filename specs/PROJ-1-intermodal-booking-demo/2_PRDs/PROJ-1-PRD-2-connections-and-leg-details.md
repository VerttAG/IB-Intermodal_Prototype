# PROJ-1-PRD-2: Connections and leg details

## Status: Planned

Covers the connection list and the connection details of step 1 (the most important part of the demo). Source: [docs/PRD.md](../../../docs/PRD.md) sections 4 and 12, [docs/user-stories.md](../../../docs/user-stories.md) stories 6–11. Story numbers are given in brackets. All trips are calculated live by the trip engine ([PROJ-1-PRD-9](PROJ-1-PRD-9-trip-engine.md)).

A trip has up to three legs: **first leg** (Vertt ride or walk) → **train** → **last leg** (Vertt ride or walk).

## User Stories

### US-1: As a customer, I want to see the best ways to make my journey side by side so that I can choose the one that suits me (stories 6, 27)
**Given** start, destination, time and travelcard are set and I pressed "Search"
**When** I look at the connection list
**Then** I see up to three bookable trips labelled Fastest / Cheapest / Greenest
**And** below them two comparison cards

**Acceptance Criteria:**
- [ ] AC-1: The list shows, in this order: up to three **bookable trips** labelled "Fastest", "Cheapest" and "Greenest" (calculated, PROJ-1-PRD-9 US-4), then **"Vertt only"**, then **"Public transport only"**.
- [ ] AC-2: A trip that wins several labels is shown once with all of them. Other calculated candidate trips are not shown.
- [ ] AC-3: Each card shows departure, arrival, duration (door to door), number of transfers, transport mode icons (car / walk / train / bus), total price and total CO₂.
- [ ] AC-4: The two comparison cards are marked "for comparison", are **not bookable and not clickable**.
- [ ] AC-5: Tapping a bookable card opens its details (US-2).
- [ ] AC-6: If a comparison cannot be calculated (e.g. OJP finds no public-transport connection), its card is left out with a short note.

### US-2: As a customer, I want to see every leg in detail so that I know what happens and where I need to be (story 7)
**Given** I opened the details of a trip
**When** I look at the legs
**Then** each leg shows who carries me, from where to where and when
**And** I see how much time I have at each transfer

**Acceptance Criteria:**
- [ ] AC-7: Each leg shows carrier (Vertt / SBB / walk), mode icon, from → to, departure, arrival and duration.
- [ ] AC-8: Train legs show the line (e.g. S11, IC 8) as delivered by OJP (PROJ-1-PRD-6).
- [ ] AC-9: Vertt legs show the car category. Prototype 1 has one category, "Vertt".
- [ ] AC-10: The car of a Vertt leg is drawn from the **car pool** (PROJ-1-PRD-7) once per Vertt leg and stays the same until the run ends.
- [ ] AC-11: Walk legs show the walking time and distance; price CHF 0.00 and CO₂ 0.0 kg.
- [ ] AC-12: Before a Vertt leg, the assumed waiting time for the car is visible (e.g. "car arrives in 5 min").
- [ ] AC-13: Between two legs a transfer row shows the minutes available (at least 8 min before a train).
- [ ] AC-14: From the details I can continue to the next step or go back to the connection list.
- [ ] AC-15 *(Could)*: A transfer longer than 15 min is marked "long wait".
- [ ] AC-16 *(Could)*: Train legs show the platform if OJP delivers it.

### US-3: As a customer, I want to see what each leg costs and what I pay in total so that I understand the price and can compare (story 8)
**Given** a trip is shown
**When** I look at the prices
**Then** I see a price per leg and a clear total
**And** I see when my travelcard changed the train price

**Acceptance Criteria:**
- [ ] AC-17: Each leg shows its price in CHF with two decimals, rounded to CHF 0.05. Vertt prices come from the Vertt API (calculated with the tariff, PROJ-1-PRD-7), train prices from OJP Fare (PROJ-1-PRD-6).
- [ ] AC-18: The total equals the sum of the rounded leg prices. There are no other amounts.
- [ ] AC-19: With half-fare the train leg carries the hint "half-fare price". With GA it shows CHF 0.00 and "covered by GA".
- [ ] AC-20: The two comparison cards also show a total price; "Public transport only" follows the travelcard.

### US-4: As a customer, I want to see how much CO₂ each leg and the whole journey cause so that I can choose a climate-friendly trip (story 9)
**Given** a trip is shown
**When** I look at the CO₂ values
**Then** I see kg CO₂ per leg and in total, per person

**Acceptance Criteria:**
- [ ] AC-21: CO₂ is shown in kg with one decimal, per person, per leg and as a total.
- [ ] AC-22: CO₂ of a Vertt leg = distance (Valhalla) × CO₂ factor of the pool car. Electric cars show 0.0 kg.
- [ ] AC-23: CO₂ of a train leg follows CTO topic B7: 0.0 kg (tailpipe rule) or the OJP value. The OJP value is always stored in the data link.
- [ ] AC-24: A value that cannot be calculated shows "not available", never 0.
- [ ] AC-25: No comparison text is shown (no "saves X kg").

### US-5: As a customer, I want to see my whole journey on a map so that I understand where the car takes me, where I change and where the train goes (story 10)
**Given** I opened the details of a bookable trip
**When** I look at the map
**Then** I see all legs coloured by carrier, with start, transfer points and destination marked

**Acceptance Criteria:**
- [ ] AC-26: A map is shown for bookable trips only, in the details and in the overview (PROJ-1-PRD-3).
- [ ] AC-27: Each leg is coloured by carrier (Vertt, SBB, walk) and a legend explains the colours.
- [ ] AC-28: Vertt legs follow the streets (route from Valhalla), train legs follow the railway line (from OJP), walk legs follow the footpath (from OJP). If no geometry is available, the leg is a straight line and is marked as such.
- [ ] AC-29: Markers show start address, each station and destination address.
- [ ] AC-30: The map opens zoomed so the whole journey is visible. Legs are not highlighted on interaction.

### US-6: As a customer, I want to see what makes the offered trips special so that I understand the benefit of booking Vertt and SBB together (story 11, Should)
**Given** the connection list is shown
**When** I look at a bookable trip
**Then** I see its labels and that it is door to door with one booking

**Acceptance Criteria:**
- [ ] AC-31: Bookable trips carry their labels (Fastest / Cheapest / Greenest) and the fixed text "Door to door with one booking". There is no separate "Recommended" tag.

## Edge Cases
- Both ends are walks (start and destination close to stations): a train-only trip; shown like any other trip (PROJ-1-PRD-9 AC-20).
- A trip has one Vertt leg or two: list, details and map work for all shapes.
- The pool car is electric: Vertt leg shows 0.0 kg (a real value).
- A train price is "not available" (PROJ-1-PRD-6): the trip is not offered (PROJ-1-PRD-9 AC-19).
- GA: the train leg is CHF 0.00, so the total is the Vertt part only.
- Only one trip could be built: it carries all three labels.
- The map tiles cannot be loaded (no internet in the meeting room): legs, prices and CO₂ stay readable and booking still works.
- A transfer has 0 or negative minutes: a calculation error; the trip must not be offered.

## Open Questions
- **Total CO₂ when one leg is "not available":** show "not available" for the total (proposed), or the sum of the known legs with a note? With every pool car having a CO₂ factor this should only happen if OJP or Valhalla fail. → Tim.
- Should estimated or placeholder values be marked on screen (cto-meeting B1)?
- CO₂ method for trains: 0.0 kg (tailpipe) or the OJP value (cto-meeting B7)?

## Dependencies
- Requires: PROJ-1-PRD-9 (trips and labels – the only source of the list), PROJ-1-PRD-1 (inputs), PROJ-1-PRD-6 (train legs, prices, walk legs, public-transport comparison), PROJ-1-PRD-7 (Vertt legs, prices, car, street geometry).
- Feeds: PROJ-1-PRD-3 (legs, prices, CO₂ and map reused in the overview), PROJ-1-PRD-5 (legs, car, sources and assumptions in the data link).
- Open: GitHub issue #14 (CO₂ unit of the car data).

## Technical Requirements
- Every number on screen can be traced to its source (PRD definition of done).
- Carriers are never told apart by colour alone: leg rows name the carrier and the map has a legend.
- The list and the details are usable without the map.
- The car pool holds make, model, year and CO₂ factor only – no number plates.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: connection cards on screen "plan" and screen "detail" of the lite mockup, [mockup/index.html](../../../mockup/index.html), live at https://ib-intermodal-prototype.vercel.app.
- New component candidates: label tags (several per card), walk leg row, waiting-time hint, "not available" value, marker for straight-line legs, loading state of the list.
- Design tokens: none defined yet; the mockup uses one colour each for Vertt, SBB and bus – walk needs one more.
- Interaction contract: bookable card opens details, comparison cards inert, back to list, continue, map fitted to the journey.
- Implementation tolerance: layout and wording may change; order of the cards, the "for comparison" marking and the rounding rules may not.
