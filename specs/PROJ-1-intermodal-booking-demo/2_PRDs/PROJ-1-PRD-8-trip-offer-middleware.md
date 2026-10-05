# PROJ-1-PRD-8: Trip offer middleware and AI station choice

## Status: Planned

A service of our own on the server, between the partner interfaces and the booking app. It runs the **trip engine** ([PROJ-1-PRD-9](PROJ-1-PRD-9-trip-engine.md)): it gets the leg offers of SBB (PROJ-1-PRD-6) and Vertt (PROJ-1-PRD-7), builds whole trips, calculates totals and labels, and serves them to the app. It also asks an **AI model which stations are worth trying** for a journey. Source: [docs/user-stories.md](../../../docs/user-stories.md) stories 27, 28, 29.

The model is **Jev 1.13** by TypeSafe, called through **OpenRouter** (`typesafe/jev-1.13`). It **does not** decide the labels Fastest / Cheapest / Greenest – those are calculated (decided by Tim 2026-10-05).

## What we know about the model

Checked on 2026-10-05 against OpenRouter and the TypeSafe documentation.

| Fact | Consequence |
|---|---|
| Jev is a **decision model**: it picks one of the options it is given, with a probability. It does not write text and cannot invent options. | The middleware builds a list of real stations (from OJP); the model only **chooses** among them. It cannot name a station that does not exist. |
| Its documentation says it is **not reliable with numbers, dates and times** ("not a calculator", "keep the arithmetic in code"). | All calculations stay in code. Choosing stations that "make sense for the route" is a judgement, which suits the model better than comparing totals. |
| Its answer can depend on the **order** of the options. | The choice must be the same when the stations are listed in another order (AC-12). |
| Extra, unrelated content lowers its accuracy; limit 32,000 tokens per request. | Only the values needed for the choice are sent. |
| Price: USD 0.042 per million input tokens, output free. | Cost is negligible for a demo. |
| It is **not** called like a chat model: OpenRouter serves it on its own "decisions" endpoint (marked alpha). | An alpha endpoint can change → the code fallback (AC-14) matters. Risk accepted 2026-10-05. |

**Earlier trial (2026-10-05, labels task):** asked to pick fastest / cheapest / greenest from calculated totals, the model was right in 210 of 210 decisions (median answer time 0.3 s, slowest 1.6 s); adding up raw legs itself, it was right in 92 %. All wrong answers had a certainty of 0.76 or lower. The station task has **not been tried yet** (open question).

## User Stories

### US-1: As a partner app, I want one service that returns complete trip offers so that I don't have to combine the partners' leg offers myself (story 28)
**Given** start and destination address, departure time and travelcard
**When** the booking app asks the middleware
**Then** it gets up to three labelled trips and the two comparison cards

**Acceptance Criteria:**
- [ ] AC-1: The middleware runs the trip engine as specified in PROJ-1-PRD-9 and returns its result: labelled trips, comparison cards, and for each trip all legs, totals, labels and assumptions.
- [ ] AC-2: It gets Vertt legs only from the Vertt API (PROJ-1-PRD-7) and train legs, walk legs and prices only from OJP and OJP Fare (PROJ-1-PRD-6). It holds no leg data of its own.
- [ ] AC-3: The answer is JSON and documented in `docs/api/trip-offers.md`.
- [ ] AC-4: The middleware is not a public service (decided 2026-10-05): one entrance for our own frontend, which only returns trip offers.
- [ ] AC-5: Requests from other websites are refused, and the number of searches one visitor can make is limited.
- [ ] AC-6: Everything behind the entrance – Vertt API, OJP, OJP Fare, Valhalla and the model – is called from the server only, with secrets the browser never sees.

### US-2: As a customer, I want the AI to pick the stations worth trying so that I get a good trip even when the nearest station is not the best one (story 29)
**Given** start and destination are known
**When** the middleware looks for candidate stations
**Then** it builds a list of real stations and the model chooses which ones to try

**Acceptance Criteria:**
- [ ] AC-7: Per side (start and destination), the code builds an option list from OJP: the nearest stations with train service (about 10) and the hub stations within ~30 km. Each option has name, stop ID, distance to the address and whether it is a hub.
- [ ] AC-8: The model chooses per side **1 hub** (if one is in the list) and **2 stations that make sense for the route** – e.g. in the direction of travel or with better connections.
- [ ] AC-9: The model receives the start and destination address (all trips are mock trips – decided by Tim 2026-10-05), the option lists and the direction of travel. Nothing about the customer's login, payment or travelcard.
- [ ] AC-10: Only stations from the option list are accepted. Anything else in the answer is ignored.
- [ ] AC-11: Each choice is returned with the model name, version and how sure the model was.
- [ ] AC-12: The same addresses and options lead to the same choice, also when the options are listed in a different order. Choices are cached during a demo.

### US-3: As a demo presenter, I want the search to work even when the model fails so that a demo never breaks because of the AI (story 29)
**Given** the model is asked for stations
**When** it is not sure, too slow or unreachable
**Then** the code chooses the stations instead

**Acceptance Criteria:**
- [ ] AC-13: If the model chooses fewer valid stations than needed, the code fills up: the nearest hub within ~30 km, then the nearest stations.
- [ ] AC-14: If the model is below the certainty threshold (**0.8**), does not answer within the time limit (**2 s**), or cannot be reached, the code chooses all stations (AC-13). The customer still gets trips. Both values are configurable.
- [ ] AC-15: For each candidate station, the server log records where it came from: "model" or "code fallback". It is not part of the data link (PROJ-1-PRD-5 contains only transactional data).
- [ ] AC-16: How often the model was used, unsure or unavailable can be read out after a demo.

## Edge Cases
- No hub within ~30 km: the model chooses 3 nearby stations.
- Fewer than 3 stations with train service near an address (remote area): fewer candidates; the engine works with what there is.
- The start or destination is itself a station: it is always one of the candidates.
- The model picks the same station for both sides: that combination is skipped (no train needed).
- The model answers something unusable: treated like "no answer" (AC-14).
- Someone calls the entrance from outside our frontend, or very often: refused or slowed down (AC-5); the partner interfaces and the model are not reached.
- OpenRouter's limit or credit is used up during a demo: AC-14 applies; the presenter sees no error page.

## Open Questions
- **Spike first (decided by Tim 2026-10-05):** before building, try the station task on 5–10 example journeys (e.g. Wettswil am Albis → Bern, Winterthur → Luzern, a Basel suburb → Zürich Flughafen). The code builds the option lists with detour values, Jev chooses, Tim judges the choices. Uses Aleksandar's OpenRouter key (`OPENROUTER_API_KEY` in `.env`, never committed).
- Confirm in the spike: certainty threshold 0.8 and time limit 2 s for the station task; whether the model needs more context per station (e.g. lines, trains per hour – costs OJP calls).
- Data sent to OpenRouter (mock addresses, station names) leaves Switzerland – OK for Vertt and the partners? → CTO.
- Answered 2026-10-05 (Tim): time limit 2 s · certainty threshold 0.8 · **password gate stays on** (`mockup/middleware.js`, password in Vercel as `DEMO_PASSWORD`, known to Tim and Aleksandar).

## Dependencies
- Requires: PROJ-1-PRD-6 (stations, trains, prices), PROJ-1-PRD-7 (Vertt offers), PROJ-1-PRD-9 (trip engine rules), an OpenRouter account with credit and an access key.
- Feeds: PROJ-1-PRD-2 (connection list, details), PROJ-1-PRD-3 (overview), PROJ-1-PRD-5 (amounts per operator).

## Technical Requirements
- The OpenRouter key never appears in the page, the repo, a data link or an export. The middleware runs on a server, not in the browser.
- The model version is fixed (Jev 1.13), not "latest", so results do not change unnoticed between demos.
- All money, time and CO₂ calculations are done by the middleware, never by the model.
- A search shows its result within about 5 s, with a loading state (PROJ-1-PRD-9).

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: the connection card of the lite mockup, [mockup/index.html](../../../mockup/index.html).
- New component candidates: none of its own; optionally a small note on a trip "stations chosen by AI".
- Design tokens: none defined yet.
- Interaction contract: none of its own.
- Implementation tolerance: how the option list is built may change; the rule that the model only chooses among real stations (AC-10) may not.
