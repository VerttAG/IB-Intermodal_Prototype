# PROJ-1-PRD-8: Trip offer middleware with model decision

## Status: Planned

> **Changed by [PROJ-1-PRD-9](PROJ-1-PRD-9-trip-engine.md) (Tim, 2026-10-05):** the model **no longer chooses the labels** – Fastest / Cheapest / Greenest are decided by calculation only (US-3 and US-4 below are replaced by PRD-9 US-4). The model gets a judgement task instead: it **proposes candidate stations** (1 hub within ~30 km + 2 stations that make sense for the route), each checked against OJP, with a code fallback (PRD-9 US-2). The middleware's role in US-2 (building trips, one private entrance, keys on the server), the trial results and the privacy rule AC-15 still apply. Where this PRD differs, PRD-9 wins.

A service of our own that sits between the partner interfaces and the booking app. It collects the leg offers of SBB (PROJ-1-PRD-6) and Vertt (PROJ-1-PRD-7), combines them into whole trips, asks an AI model which trip is the **fastest**, the **cheapest** and the **greenest**, and serves these trip offers to the app. Source: [docs/user-stories.md](../../../docs/user-stories.md) stories 27, 28, 29 (proposed, v1.1).

The model is **Jev 1.13** by TypeSafe, called through **OpenRouter** (`typesafe/jev-1.13`).

## What we know about the model

Checked on 2026-10-05 against OpenRouter and the TypeSafe documentation.

| Fact | Consequence |
|---|---|
| Jev is a **decision model**: it picks one of the options it is given, with a probability. It does not write text and cannot invent a trip. | The middleware builds the possible trips; the model only chooses among them. |
| Its documentation says it is **not reliable with numbers, dates and times** ("not a calculator", "keep the arithmetic in code", "do not ask something code can compute exactly"). | Fastest, cheapest and greenest are number comparisons. The middleware calculates all totals itself and **checks every model decision** against them (US-4). |
| Its answer can depend on the **order** of the options. | A decision must be the same when the trips are listed in another order (AC-17). |
| Extra, unrelated content lowers its accuracy; limit 32,000 tokens per request. | Only the few values needed for the decision are sent. |
| Price: USD 0.042 per million input tokens, output free. | Cost is negligible for a demo. |
| It is **not** called like a chat model: OpenRouter serves it on its own "decisions" endpoint (marked alpha). | Tried out successfully, see below. An alpha endpoint can change → the fallback in AC-21 matters. |

## Trial on 2026-10-05

Real calls to `typesafe/jev-1.13` through OpenRouter, each asking for fastest, cheapest and greenest in one request. The answers were compared with the calculated result.

| What the model received | Trips per request | Correct decisions | Answer time (median) |
|---|---|---|---|
| **Calculated totals** per trip – realistic set (4 Vertt rides × 3 trains), 10 different orders | 12 | 30 of 30 | 0.3 s |
| **Calculated totals** – random values, also with values close together | 3 / 6 / 12 | 180 of 180 | 0.3 s |
| **Raw legs** – the model has to add up the legs itself | 3 / 6 / 12 | 124 of 135 (92 %) | 0.3 s |

- With calculated totals the model was always right, in every order, and sure of it (lowest certainty 0.80).
- When it had to add up legs itself it was wrong in 1 of 12 decisions. All wrong answers had a certainty of 0.76 or lower.
- Slowest single answer: 1.6 s. Cost of all 115 requests: under USD 0.01.
- This is a small trial with made-up values, not a guarantee. It confirms AC-14 (send totals, not legs) and that the check in US-4 costs nothing and catches the remaining risk.

## User Stories

### US-1: As a customer, I want to see the fastest, the cheapest and the greenest way to make my journey so that I can pick by what matters to me (story 27)
**Given** start, destination, time and travelcard are set
**When** the connections are shown
**Then** I see the trip offers labelled "Fastest", "Cheapest" and "Greenest"

**Acceptance Criteria:**
- [ ] AC-1: The Vertt + SBB connections are shown as up to three trip offers, labelled "Fastest", "Cheapest" and "Greenest".
- [ ] AC-2: If one trip earns several labels, it is shown once with all its labels.
- [ ] AC-3: Each offer shows what PROJ-1-PRD-2 requires of a connection card: times, duration, transfers, modes, total price, total CO₂.
- [ ] AC-4: Every labelled offer can be opened and booked like the bookable connection in PROJ-1-PRD-2 and PROJ-1-PRD-3.
- [ ] AC-5: When the travelcard changes, prices and labels are updated; the "Cheapest" label may move to another trip.
- [ ] AC-6: A label is never shown on a trip that does not deserve it: "Fastest" has the earliest arrival for the chosen departure (shortest total duration), "Cheapest" the lowest total price, "Greenest" the lowest total CO₂.

### US-2: As a partner app, I want one service that returns complete trip offers so that I don't have to combine the partners' leg offers myself (story 28)
**Given** a start, a destination, a departure time and a travelcard
**When** I ask the middleware for trip offers
**Then** I get complete, bookable trips built from the partners' leg offers
**And** each says which labels it carries

**Acceptance Criteria:**
- [ ] AC-7: The middleware gets the Vertt leg offers from the Vertt API (PROJ-1-PRD-7) and the train legs and prices from OJP and OJP Fare (PROJ-1-PRD-6). It holds no leg data of its own.
- [ ] AC-8: It combines the leg offers into whole trips. A trip is only built if every transfer has at least 8 minutes.
- [ ] AC-9: It calculates for every trip: total duration, total price (sum of the rounded leg prices) and total CO₂.
- [ ] AC-10: Its answer contains every offered trip with all legs, the leg offers they came from, the totals, and the labels.
- [ ] AC-11: The booking app gets its trip offers only from the middleware, and the middleware's answer is enough to show the list, the details and the overview.
- [ ] AC-12: The answer is JSON and documented in `docs/api/trip-offers.md`.
- [ ] AC-12a: The middleware is not a public service (decided 2026-10-05): it has exactly one entrance, for our own frontend, and that entrance only returns trip offers.
- [ ] AC-12b: Requests from other websites are refused, and the number of requests one visitor can make is limited.
- [ ] AC-12c: Everything behind the entrance – the Vertt API, OJP, OJP Fare, the route service and the model – is called from the server only, with secrets the browser never sees.

### US-3: As a demo presenter, I want the labels to be decided by the AI model so that I can show a model working on real partner offers (story 29)
**Given** the middleware has built the possible trips
**When** it needs to label them
**Then** it asks Jev 1.13 through OpenRouter which trip is the fastest, which the cheapest and which the greenest
**And** it passes the model's decision on

**Acceptance Criteria:**
- [ ] AC-13: For each of the three labels, the model is asked to choose one of the trips the middleware built. The model never receives a trip the customer could not book.
- [ ] AC-14: The model receives the totals the middleware calculated (duration, price, CO₂), not raw leg data it would have to add up.
- [ ] AC-15: Nothing about the customer is sent to the model or to OpenRouter: no customer ID, no login, no typed address, no travelcard holder – only trip values.
- [ ] AC-16: Each decision is returned with the model's name and version and how sure the model was.
- [ ] AC-17: Listing the same trips in a different order leads to the same labels.
- [ ] AC-18: The same question with the same trips gives the same labels every time during a demo.

### US-4: As Vertt, I want every model decision checked against the numbers so that the demo never shows a wrong "cheapest" (story 29)
**Given** the model has made its three decisions
**When** the middleware prepares its answer
**Then** each decision is compared with the calculated result
**And** a wrong or missing decision never reaches the customer

**Acceptance Criteria:**
- [ ] AC-19: The middleware works out the correct trip for each label from its own totals.
- [ ] AC-20: If the model's choice differs from the calculated one, the calculated one is shown, and the difference is recorded.
- [ ] AC-21: If the model is not sure enough, does not answer in time or cannot be reached, the calculated result is shown instead. The customer still gets the trip offers.
- [ ] AC-22: For each label the answer says where it came from: "model, confirmed", "model overruled" or "calculated, model not available".
- [ ] AC-23: A booking stores, for the chosen trip, its labels and where each came from (PROJ-1-PRD-5).
- [ ] AC-24: How often the model was confirmed, overruled or unavailable can be read out after a demo.

## Edge Cases
- Only one trip can be built: it carries all three labels and no model is asked.
- Two trips have the same total for a label (same price, same duration or same CO₂): a fixed rule breaks the tie (proposed: the earlier arrival, then the lower price); the model's choice counts as confirmed if it picked either.
- A trip has a leg whose CO₂ is "not available" (3 of the 9 cars in the Vertt data): it cannot be "Greenest". If no trip has a complete CO₂ value, no "Greenest" label is shown.
- A trip has no train price (PROJ-1-PRD-6 AC-24): it is not offered and not sent to the model.
- All trips have 0.0 kg CO₂ on the train legs (tailpipe rule): "Greenest" is decided by the Vertt legs alone.
- GA: all train prices are CHF 0.00, so "Cheapest" is decided by the Vertt legs alone.
- A promo code (PROJ-1-PRD-3) is applied after the trip was chosen and does not change the labels.
- The model chooses a trip that is not in the list, or answers something unusable: treated like "no answer" (AC-21).
- No trip can be built at all: the middleware says so clearly (PROJ-1-PRD-1 AC-8).
- Someone calls the entrance from outside our frontend, or very often: refused or slowed down (AC-12b); the partner interfaces and the model are not reached.
- OpenRouter's limit or credit is used up during a demo: AC-21 applies; the presenter is not shown an error page.

## Open Questions
- **What should the model really decide?** Its makers say not to use it for comparing numbers, and with the check in US-4 the result on screen is always the calculated one. Two ways to give the model a real job: (a) keep the three labels as specified here and present the model as a second opinion with a visible success rate; (b) add a fourth label, **"Recommended"**, where the model weighs duration, price, CO₂ and transfer comfort – a judgement, not a calculation, and what this kind of model is built for. → Tim / CTO.
- **When the model disagrees with the numbers:** always show the calculated result (proposed, AC-20), or show the model's choice and mark it? → Tim.
- **Three labelled offers and the old list.** Story 6 has one bookable connection plus two comparisons; story 11 marks it "recommended". Proposed: the labelled offers replace the single bookable connection; the two comparison cards stay. → Tim.
- **How many trips to choose from?** With the provided data there are few: e.g. 4 recorded rides Wettswil am Albis → Zürich HB with different cars and prices, times the next trains. Is that enough for a convincing demo, or should cheaper/slower train options (regional trains, saver vs normal ticket) be included on purpose?
- **How sure is sure enough** for AC-21? The trial suggests a threshold around 0.8 (right answers were at 0.80 or above, wrong ones at 0.76 or below). To be confirmed with real partner offers.
- ~~The OpenRouter endpoint for the model is marked alpha~~ → **Risk accepted 2026-10-05.** If it changes or is withdrawn, TypeSafe's own interface takes the same request, and AC-21 keeps the demo running meanwhile.
- **How private can the middleware be?** Decided: not public (AC-12a to AC-12c). But the page runs in the customer's browser, so the one entrance it calls can technically be called by anyone who looks it up. **Proposed: a user name and password in front of the whole demo** (browser's built-in login box, "basic auth"). It is possible on Vercel's free plan with a few lines of our own in front of the app; Vercel's ready-made password protection is a paid add-on of the Pro plan. Consequences: presenters and partners need the password; every request of the page, including the one to the middleware, then carries it. Switch it on? → Tim / CTO.
- Data sent to OpenRouter leaves Switzerland. It contains no personal data (AC-15) – still OK for Vertt and the partners? → CTO.

## Dependencies
- Requires: PROJ-1-PRD-6 (train legs and prices), PROJ-1-PRD-7 (Vertt leg offers – all offers of a route, not one).
- Feeds: PROJ-1-PRD-2 (connection list, details), PROJ-1-PRD-3 (overview), PROJ-1-PRD-5 (labels and their origin in the data link).
- External: an OpenRouter account with credit and an access key.
- Changes: PROJ-1-PRD-2 (one bookable connection → up to three labelled offers), PROJ-1-PRD-7 (which ride backs an offer is no longer drawn at random).

## Technical Requirements
- The OpenRouter key never appears in the page, the repo, a data link or an export. The middleware therefore runs on a server, not in the browser.
- The connection list appears within about 2 seconds of a change, including the model decision; a travelcard change feels immediate (PROJ-1-PRD-1 AC-15). If the model takes longer, AC-21 applies.
- The model version is fixed (Jev 1.13), not "latest", so that results do not change unnoticed between demos.
- A demo can be repeated without internet access to the model, using the stored decisions (AC-18).
- All money and time calculations are done by the middleware, never by the model.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: the connection card of the lite mockup, [mockup/index.html](../../../mockup/index.html); its "Recommended" tag becomes the place for the labels.
- New component candidates: label tags "Fastest", "Cheapest", "Greenest" (several on one card); a small mark showing that a label was decided by the model. Neither is in the mockup.
- Design tokens: none defined yet.
- Interaction contract: labels update when the travelcard changes; every labelled card opens its details.
- Implementation tolerance: wording and look of the labels may change; the rule that a label is never wrong (AC-6) may not.
