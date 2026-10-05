# PROJ-1-PRD-1: App choice and journey inputs

## Status: Planned

> **Changed by [PROJ-1-PRD-9](PROJ-1-PRD-9-trip-engine.md) (Tim, 2026-10-05):** start and destination are address fields with typing and swisstopo suggestions (pre-filled with an example); no "use my location"; the customer chooses the "depart at" date and time. Place lists, preset scenario times and the snap to known places no longer apply. Where this PRD differs, PRD-9 wins.

Covers step 0 and the input part of step 1. Source: [docs/PRD.md](../../../docs/PRD.md) section 4, [docs/user-stories.md](../../../docs/user-stories.md) stories 1a, 2, 3, 4, 5. Story numbers are given in brackets.

## User Stories

### US-1: As a demo presenter, I want to choose whether the booking happens in the Vertt app or the SBB app so that I can show how the settlement changes with the seller (story 1a)
**Given** a new run has started
**When** I choose "Vertt app" or "SBB app"
**Then** the planning screen opens and every following screen shows which app is used
**And** the choice cannot be changed until the run ends

**Acceptance Criteria:**
- [ ] AC-1: Step 0 offers exactly two options, "Vertt app" and "SBB app", each saying that this operator sells the whole journey.
- [ ] AC-2: Every screen after step 0 shows the name of the chosen app.
- [ ] AC-3: No screen after step 0 offers a way to change the app. Only "New booking" on the receipt or a page reload returns to step 0.
- [ ] AC-4: Apart from the app name and the seller wording, all screens are identical in both apps: one neutral design, no official Vertt or SBB logos.

### US-2: As a customer, I want to set where my journey starts and ends so that I get a door-to-door connection, not just station to station (story 2)
**Given** I am on the planning screen
**When** I set a start and a destination
**Then** the connections for this combination are shown
**And** if my place is not a known place, the nearest known place is used and I am told so

**Acceptance Criteria:**
- [ ] AC-5: Start and destination can each be set, including known places that are not stations. The known places are the places Vertt serves (PROJ-1-PRD-7) and official stations (PROJ-1-PRD-6); the app keeps no place list of its own.
- [ ] AC-5a: The customer can type an address. While typing, a list of matching official Swiss addresses is suggested; choosing one sets the place. Nothing is taken over without the customer choosing it.
- [ ] AC-5b: The chosen address is turned into coordinates, and the coordinates – not the address – are passed on to get the Vertt offers (PROJ-1-PRD-7).
- [ ] AC-5c *(Could)*: Instead of typing, the customer can use the current position of the device. The address found for that position is shown so the customer can check it.
- [ ] AC-5d: Typing is the one exception to the rule "nothing has to be typed": a pre-filled start and destination let a presenter click through without typing.
- [ ] AC-6: If the input is not a known place, the nearest known place is used and a message names it with the distance (e.g. "We use Wettswil am Albis, 2.1 km from your address").
- [ ] AC-7: If the nearest known place is farther away than the maximum snap distance, a message says the area is not covered and no connections are shown.
- [ ] AC-8: If there is no connection for a combination, a message says so and no connections are shown.
- [ ] AC-9: There is no swap button.
- [ ] AC-10: Changing start or destination updates the connection list immediately, without a separate search button.
- [ ] AC-11: An address entered by the customer is never stored, and never appears in the data link or the export (see PROJ-1-PRD-5).

### US-3: As a customer, I want to see when I travel so that the connections fit my plans (story 3)
**Given** I am on the planning screen
**When** I look at the travel time
**Then** I see date and time as "depart at", pre-filled with the scenario time
**And** I can see that it is fixed in the demo

**Acceptance Criteria:**
- [ ] AC-12: Date and time are shown labelled "Depart at", pre-filled with the scenario time of the chosen route.
- [ ] AC-13: The value cannot be edited and carries a lock icon with the hint "fixed in demo".

### US-4: As a customer, I want to state which travelcard I have so that I see the price I actually pay (story 4)
**Given** I am on the planning screen
**When** I choose no travelcard, half-fare or GA
**Then** all prices update immediately
**And** only the SBB part changes

**Acceptance Criteria:**
- [ ] AC-14: Three options are offered: no travelcard, half-fare, GA. Half-fare is selected when a run starts.
- [ ] AC-15: Changing the travelcard updates every price on the screen at once (all connection cards).
- [ ] AC-16: The price of every Vertt leg is the same for all three travelcards.
- [ ] AC-17: The chosen travelcard is shown again in the overview (PROJ-1-PRD-3) and stored in the data link (PROJ-1-PRD-5).

### US-5: As a customer with a SwissPass, I want to log in with it while planning so that my travelcard is filled in and I don't log in again before paying (story 5)
**Given** I am on the planning screen and not logged in
**When** I click "Log in with SwissPass" and pick a test profile
**Then** the travelcard of that profile is set and locked
**And** the login step is skipped later

**Acceptance Criteria:**
- [ ] AC-18: The planning screen has a "Log in with SwissPass" button in both apps.
- [ ] AC-19: After the click, three test profiles are offered: no travelcard, half-fare, GA.
- [ ] AC-20: Picking a profile sets the travelcard, updates all prices, and locks the travelcard with the hint "from SwissPass".
- [ ] AC-21: After the SwissPass login the button is gone and there is no log-out within the run.
- [ ] AC-22: After the SwissPass login, "Continue" from the connection details leads straight to the overview; step 2 is not shown.
- [ ] AC-23: The booking stores `login_method = swisspass` and the travelcard of the profile.

## Edge Cases
- Start and destination are the same place, or both snap to the same known place: treated as "no connection" (AC-8).
- The typed text matches no address: the list says so; the previous place stays.
- The customer types but picks nothing from the list: the place is not changed.
- The address search does not answer: a message says so; the pre-filled places still work.
- The device position is refused or not available (AC-5c): the customer can still type.
- The position has no building nearby (e.g. inside a station hall or in a field): the locality is shown instead of an address.
- The profile box is opened and closed without picking a profile: nothing changes, travelcard stays editable.
- A SwissPass profile differs from the travelcard chosen before: the profile wins, prices update.
- Start or destination is changed after the connection details were opened: the list shows the new combination; nothing from the old one is kept.
- The page is reloaded in the middle of a run: the run starts again at step 0, nothing is booked or stored.
- The car for the run (PROJ-1-PRD-2) is drawn once per run and does not change when places or travelcard change.

## Open Questions
- **Address search – decided 2026-10-05: swisstopo.**
- **Typed address – decided 2026-10-05:** the customer enters an address, it is turned into coordinates and these go to the Vertt API. The lite mockup still shows a dropdown. Trial and findings: [docs/api/geocoding.md](../../../docs/api/geocoding.md).
- **Is "use my location" (AC-5c) wanted?** It is the only case that needs reverse geocoding (coordinates → address). Typing an address needs the forward direction only. → Tim.
- Addresses outside Switzerland cannot be found by the address search: treated as "area not covered" (AC-7).
- **Places.** With the Vertt tariff known (PROJ-1-PRD-7), Vertt offers can be calculated for any address in the area Vertt serves, once a route service is chosen. Until then only the recorded routes work (Wettswil am Albis and four stations). Which destinations does Prototype 1 offer on the train side: a fixed list of stations, or any Swiss station through OJP? → Tim / CTO.
- What is the maximum snap distance (cto-meeting T2, question 3)?

## Dependencies
- Requires: PROJ-1-PRD-2 (connection list shown on the same screen), PROJ-1-PRD-7 (places Vertt serves), PROJ-1-PRD-6 (stations).
- Feeds: PROJ-1-PRD-3 (login skip, travelcard in overview), PROJ-1-PRD-5 (`system`, `login_method`, `travelcard` in the data link).
- Open decision: cto-meeting T2 (how Vertt legs are created, known places).

## Technical Requirements
- Phone layout; on a laptop the phone-sized screen sits in the middle of the page.
- Everything on these screens works with a pointer and with the keyboard; the locked time and locked travelcard are announced as not editable.
- No login or account data leaves the browser. A typed address goes only to the official address search (swisstopo), never to our own server; coordinates passed on are rounded to about 100 m and not stored.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: screens "app" and "plan" of the lite mockup, [mockup/index.html](../../../mockup/index.html), live at https://ib-intermodal-prototype.vercel.app.
- New component candidates: address input with suggestion list and "nearest known place" message; optional "use my location" button. Neither is in the mockup.
- Design tokens: none defined yet; the mockup's carrier colours are the only fixed values.
- Interaction contract: fixed app choice, locked time, travelcard switch updating prices, SwissPass profile box, locked travelcard.
- Implementation tolerance: layout and wording may change; the behaviours in the acceptance criteria may not.
