# PROJ-1-PRD-1: App choice and journey inputs

## Status: Planned

Covers step 0 and the input part of step 1. Source: [docs/PRD.md](../../../docs/PRD.md) sections 4 and 12, [docs/user-stories.md](../../../docs/user-stories.md) stories 1a, 2, 3, 4, 5. Story numbers are given in brackets. The trips for these inputs are calculated live by the trip engine ([PROJ-1-PRD-9](PROJ-1-PRD-9-trip-engine.md)).

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

### US-2: As a customer, I want to enter where my journey starts and ends so that I get a door-to-door trip for exactly my addresses (story 2)
**Given** I am on the planning screen
**When** I type a start and a destination address and pick them from the suggestions
**Then** trips are calculated for exactly these addresses

**Acceptance Criteria:**
- [ ] AC-5: Start and destination are address fields. While typing, matching official Swiss addresses are suggested by the swisstopo address search; choosing one sets the address. Nothing is taken over without the customer choosing it.
- [ ] AC-6: In the first version both fields start **empty**; typing is the one exception to the rule "nothing has to be typed". A pre-filled example pair is added later, once the engine has been tried (decided by Tim 2026-10-05).
- [ ] AC-7: The chosen address is turned into coordinates by swisstopo. Address and coordinates are passed to the trip engine (PROJ-1-PRD-9), which may also send them to the AI model (PROJ-1-PRD-8) – all trips in the demo are mock trips.
- [ ] AC-8: An address that swisstopo cannot find, or that lies outside Switzerland, cannot be chosen; a message says so.
- [ ] AC-9: If no trip can be built for the addresses and time, a message says so and no connections are shown.
- [ ] AC-10: There is no swap button and no "use my location" button.
- [ ] AC-11: The search starts **only** with the **"Search"** button, which is enabled once start, destination and time are set (each search costs live API calls, PROJ-1-PRD-9). While it runs, a loading state is shown. A travelcard change after a search needs no new search (AC-15).
- [ ] AC-11a: Addresses and coordinates are used only for the search; they are not stored and do not appear in the data link or the export (PROJ-1-PRD-5).

### US-3: As a customer, I want to choose when I travel so that the trips fit my plans (story 3)
**Given** I am on the planning screen
**When** I choose a date and a time
**Then** the trips depart at or after that time

**Acceptance Criteria:**
- [ ] AC-12: Date and time are chosen as **"Depart at"**. Default: today, the next full quarter hour.
- [ ] AC-13: Only dates in the current timetable period can be chosen (OJP covers only this period). There is no "arrive by".

### US-4: As a customer, I want to state which travelcard I have so that I see the price I actually pay (story 4)
**Given** I am on the planning screen
**When** I choose no travelcard, half-fare or GA
**Then** all prices update immediately
**And** only the SBB part changes

**Acceptance Criteria:**
- [ ] AC-14: Three options are offered: no travelcard, half-fare, GA. Half-fare is selected when a run starts.
- [ ] AC-15: Changing the travelcard after a search updates every price and the labels at once, **without a new search** (the engine fetches the half-fare price; no travelcard = 2 × half-fare, GA = CHF 0.00 – PROJ-1-PRD-9 AC-12).
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
- Start and destination are the same address, or very close to each other: see PROJ-1-PRD-9 (open question "very short trips").
- The typed text matches no address: the suggestion list says so; the previous address stays.
- The customer types but picks nothing from the list: the address is not changed and "Search" stays disabled until both are chosen.
- The address search does not answer: a message says so; no search is possible.
- The chosen time is in the past, or so late that no train runs anymore: the engine finds no trip → message (AC-9).
- Start, destination or time is changed after a search: the old results are cleared; the customer searches again.
- The profile box is opened and closed without picking a profile: nothing changes, travelcard stays editable.
- A SwissPass profile differs from the travelcard chosen before: the profile wins, prices update (AC-15).
- The page is reloaded in the middle of a run: the run starts again at step 0, nothing is booked or stored.

## Open Questions
- Answered 2026-10-05 (Tim): "Search" button only · fields empty in the first version, example pair later · no addresses or coordinates in the data link.
- **Later:** which example pair to pre-fill (e.g. Wettswil am Albis → Ostermundigen), once the engine has been tried.

## Dependencies
- Requires: swisstopo address search ([docs/api/geocoding.md](../../../docs/api/geocoding.md)), PROJ-1-PRD-9 (trip engine).
- Feeds: PROJ-1-PRD-2 (connection list), PROJ-1-PRD-3 (login skip, travelcard in overview), PROJ-1-PRD-5 (`system`, `login_method`, `travelcard` in the data link).

## Technical Requirements
- Phone layout; on a laptop the phone-sized screen sits in the middle of the page.
- Everything on these screens works with a pointer and with the keyboard; the locked travelcard is announced as not editable.
- The address search (swisstopo) is called from the browser (no key needed). The search request goes to our own server, which calls the partner APIs and the model (PROJ-1-PRD-8).
- No login or account data leaves the browser.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: screens "app" and "plan" of the lite mockup, [mockup/index.html](../../../mockup/index.html), live at https://ib-intermodal-prototype.vercel.app.
- New component candidates: address input with suggestion list, date/time picker ("Depart at"), "Search" button with loading state. None are in the mockup.
- Design tokens: none defined yet; the mockup's carrier colours are the only fixed values.
- Interaction contract: fixed app choice, address suggestions, search button, travelcard switch updating prices without a new search, SwissPass profile box, locked travelcard.
- Implementation tolerance: layout and wording may change; the behaviours in the acceptance criteria may not.
