# CTO Meeting – Preparation

Prototype 1 (Intermodal Booking & Settlement Data Demo). Prepared 2026-10-05.
Read first: [PRD.md](PRD.md) (1 page flow + settlement rules) · [user-stories.md](user-stories.md) (21 agreed stories).

Goal of the meeting: confirm the PRD, decide the technical approach (engine, APIs, hosting), and settle the open business topics.

---

## Part 1 – Technical decisions

### T1 · Where does the data behind the "data link" live?  ⚠️ most important

Two agreed requirements together force a decision:
- Partners must be able to **open the link** on their own computer (story 17).
- After a cancellation, the **same link** must show the **updated** content (story 18).

→ A link that carries the data inside itself (no server) **cannot change** afterwards. And data stored only in the user's browser is **not visible** to partners.
→ So the updated-link requirement needs **a small online storage** (database or key-value store) plus something that serves it.

| Option | How | Effort / cost | Note |
|---|---|---|---|
| **A** – Small backend + storage | e.g. Vercel Functions + a key-value store / Supabase / Firebase | Medium; free tiers exist | Needs hosting decision and someone to own it. Vercel's free "Hobby" plan is for non-commercial use – check the terms for Vertt. |
| **B** – Link contains the data, cancellation creates a 2nd link | Data encoded in the URL; no server | Low | Changes story 18 ("same link"). Simplest. |
| **C** – Only the export file | Partners receive export files (e.g. by email) | Lowest | Link only works in the presenter's browser. |

**To decide:** A, B or C? Who hosts? Which account (Vertt / private / project)?

### T2 · How are the Vertt legs created? ("engine")

| Option | Description | Effort | Value for Vertt later |
|---|---|---|---|
| **A** – Recorded rides | Use the 3 real recorded rides from the Excel export (original brief) | 100 % | Low – showcase only |
| **B** – Calculated in advance | Route API + Vertt price formula, calculated once for a fixed set of 10–20 known places (matches story 2 "snap to nearest known place") | ~150–170 % | High – reusable "Vertt quote" building block |
| **C** – Live for any address | Same as B, but calculated on every search | ~250–300 % + maintenance; needs backend to hide API keys | Highest, but premature for Prototype 1 |

Recommendation: **B**, validated against the 9 recorded rides ("engine within ±X % of reality").

**Questions for the CTO:**
1. What is the **Vertt tariff formula** (base, per km, per minute, minimum, surcharges)? The values in the export (1.80/km, 0.30/min) do not reproduce the ride prices.
2. Does Vertt have an **internal price/ETA (quote) API** we could use – or which routing provider does Vertt use (the export polylines are in Google format)?
3. Which **known places** should the demo cover? Maximum snap distance (e.g. 5 km)?
4. Is a changeable **time / "arrive by"** wanted later (affects engine choice)?

### T3 · API overview – which API does what

| # | Function (story) | Needed for | API options | Key / cost | Called when |
|---|---|---|---|---|---|
| 1 | **Address → coordinates** (2) | Snap a typed address to the nearest known place | **geo.admin.ch search (swisstopo)** – free, official Swiss addresses, no key · OJP LocationInformationRequest (verify address support) · OpenRouteService geocoding | swisstopo: none | Live (in browser) |
| 2 | **Station lookup** (2, 6) | Turn stations into stop IDs (SLOID) for train search | **OJP 2.0 LocationInformationRequest** | OJP key (have one; 20,000 calls/day, 50/min) | In advance |
| 3 | **Train connections** (6, 7) | Times, line, transfers, **platform** (Could), track geometry for the map | **OJP 2.0 TripRequest** | OJP key | In advance (B) / live (C) |
| 4 | **Public-transport-only alternative** (6) | Door-to-door by bus + train | **OJP 2.0 TripRequest** with coordinates as start/end | OJP key | In advance |
| 5 | **Train ticket price** (8) | Full fare / half-fare price | **OJP Fare (beta, NOVA prices)** – test environment only · fallback: public reference prices entered manually | Separate access | In advance |
| 6 | **Vertt route, km, minutes** (7, 10) | Street route for the map + inputs for price and CO₂ | **Vertt internal / Google Routes API** (matches Vertt data; paid after free allowance; storage restrictions) · **OpenRouteService** (free tier, OpenStreetMap) · OSRM demo (tests only) | Depends | In advance |
| 7 | **Vertt price** (8) | Price per Vertt leg | **Vertt tariff formula or quote API** – no external API can do this | Internal | In advance |
| 8 | **Vertt CO₂** (9) | g/km per car in the pool | **No API** – car pool from Vertt data (Excel "Car to CO2") | – | In advance |
| 9 | **Map display** (10) | Background map + drawing routes | **Leaflet** (free library) + **OpenStreetMap** tiles or **swisstopo** map tiles (free) | Fair-use limits | Live (in browser) |
| 10 | **Data link storage** (17, 18) | Serve booking JSON to partners, update after cancellation | See **T1** (Vercel + KV / Supabase / Firebase / none) | Free tiers | Live |
| 11 | **Hosting the page** | Partners open the demo | **GitHub Pages** (free, repo is public, static only) · **Vercel** (static + functions; check plan terms) · Netlify | Free tiers | – |
| 12 | Login, payment | Fake (one click) | **No API** | – | – |

Rule of thumb: everything **"in advance"** runs once on a laptop with keys in `.env` – no key is ever exposed. Everything **"live"** that needs a key requires a small backend (Vercel Functions or similar) so the key is not visible in the browser.

**To decide:** which routing provider (6), whether to request OJP Fare access (5), map tiles (9), hosting (11).

---

## Part 2 – Business and content topics

| # | Topic | Current default in Prototype 1 | Question for CTO |
|---|---|---|---|
| B1 | **Marking real vs. estimated values** (was story 21) | not decided | Should the demo mark estimated / placeholder values (always visible marker vs. presenter toggle vs. data link only)? |
| B2 | **SBB/Vertt asymmetry** | Vertt 5 % commission on train ticket; SBB none – deliberate demo decision | OK to present like this to partners? |
| B3 | **Settlement timing** | Per booking | Real world: per booking or monthly batch? |
| B4 | **Unpaid invoice** | Invoice counts as paid immediately | What happens to the B2B share if the customer never pays? |
| B5 | **Payment fees** (card / TWINT, ~1–2 %) | Ignored | Who carries them – seller only or shared? |
| B6 | **Real cancellation rules** | Full refund, no fee | SBB refund rules; Vertt fee once the driver is on the way? |
| B7 | **CO₂ method** | Tailpipe only → trains 0.0 kg | Keep, or include energy production (well-to-wheel) so car and train are compared fairly? |
| B8 | **SBB price source** | OJP if available, else reference prices | Is OJP Fare beta acceptable? Talk to SBB? |
| B9 | **Settlement data format** | Draft in PRD section 7 | Align with partners' transaction layer before building? |
| B10 | **Demo date / audience** | not decided | When and to whom do we show it first? |

### Decisions from the original brief (GitHub issues #8–#16)

| Issue | Topic | Status after user-story discussion |
|---|---|---|
| #8 | Trip 1 buffer (+8 min shift) | Depends on T2 – irrelevant with engine option B |
| #9 | Trip 2 anchor | Depends on T2 |
| #10 | Trip 3 constructed leg (Ostermundigen) | Depends on T2 |
| #11 | Vertt tariff formula | → T2 question 1 |
| #12 | SBB fare source | → B8 |
| #13 | Rail CO₂ factor | **Resolved:** tailpipe only → 0 (see B7) |
| #14 | CO₂ unit in "Car to CO2" | Still to verify |
| #15 | Timezone of Vertt timestamps | Only relevant for engine option A |
| #16 | Hosting | → T1 / T3 row 11 |

---

## Part 3 – After the meeting

1. Write decisions into the PRD (v1.0) and close the decided GitHub issues.
2. Rework the GitHub issues: one issue per user story (or group), plus technical tasks from T1–T3.
3. Start with the OJP spike, then build.
