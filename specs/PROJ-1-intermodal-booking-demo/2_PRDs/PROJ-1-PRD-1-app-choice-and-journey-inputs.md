# PROJ-1-PRD-1: App choice and journey inputs

## Status: Planned

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
- The profile box is opened and closed without picking a profile: nothing changes, travelcard stays editable.
- A SwissPass profile differs from the travelcard chosen before: the profile wins, prices update.
- Start or destination is changed after the connection details were opened: the list shows the new combination; nothing from the old one is kept.
- The page is reloaded in the middle of a run: the run starts again at step 0, nothing is booked or stored.
- The car for the run (PROJ-1-PRD-2) is drawn once per run and does not change when places or travelcard change.

## Open Questions
- **Typed address or list?** The general demo rule says "nothing has to be typed", but story 2 describes typed addresses that are snapped to a known place. The lite mockup uses a dropdown of known places only. If Prototype 1 keeps the dropdown, AC-6, AC-7 and AC-11 do not apply. → Tim / CTO.
- **Few places in the Vertt data.** The provided rides cover Wettswil am Albis and four stations only (PROJ-1-PRD-7). Which destinations does Prototype 1 offer on the train side: a fixed list of stations, or any Swiss station through OJP? → Tim / CTO.
- What is the maximum snap distance (cto-meeting T2, question 3)?

## Dependencies
- Requires: PROJ-1-PRD-2 (connection list shown on the same screen), PROJ-1-PRD-7 (places Vertt serves), PROJ-1-PRD-6 (stations).
- Feeds: PROJ-1-PRD-3 (login skip, travelcard in overview), PROJ-1-PRD-5 (`system`, `login_method`, `travelcard` in the data link).
- Open decision: cto-meeting T2 (how Vertt legs are created, known places).

## Technical Requirements
- Phone layout; on a laptop the phone-sized screen sits in the middle of the page.
- Everything on these screens works with a pointer and with the keyboard; the locked time and locked travelcard are announced as not editable.
- No login, account or address data leaves the browser.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: screens "app" and "plan" of the lite mockup, [mockup/index.html](../../../mockup/index.html), live at https://ib-intermodal-prototype.vercel.app.
- New component candidates: address input with "nearest known place" message (only if the open question is answered with "typed address").
- Design tokens: none defined yet; the mockup's carrier colours are the only fixed values.
- Interaction contract: fixed app choice, locked time, travelcard switch updating prices, SwissPass profile box, locked travelcard.
- Implementation tolerance: layout and wording may change; the behaviours in the acceptance criteria may not.
