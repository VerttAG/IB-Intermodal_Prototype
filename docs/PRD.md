# PRD – Prototype 1: Intermodal Booking & Settlement Data Demo

| | |
|---|---|
| Status | **Draft v0.3** – user stories agreed; to be confirmed with Vertt CTO |
| Owner | Tim Diethelm (Vertt AG) |
| Last update | 2026-10-05 |
| Related | [user-stories.md](user-stories.md) (what each user needs) · [cto-meeting.md](cto-meeting.md) (open topics, APIs) · [PROTOTYPE_1_BRIEF.md](PROTOTYPE_1_BRIEF.md) (original technical brief) |

This PRD **extends** the brief; where they differ, this PRD wins.

## 1. Why are we building this?

The Innovation Booster project aims at a settlement layer that bills and splits one intermodal journey (train + ride-hailing) between operators. Prototype 1 makes this tangible:

- From the **customer's view**: a clickable booking app that shows one door-to-door journey combining Vertt and SBB – route, times, price and CO₂ per carrier – similar to the SBB app.
- From the **settlement view**: every booking produces a **data link** with the full trip and all B2B money movements. The Innovation Booster partners use this data as input for their transaction layer (blockchain); Prototype 2 builds on it.

The customer pays only **one** operator. The interesting part is the **B2B settlement** between the operators – it is captured in the data, not animated.

## 2. Who uses it?

| Order | User | What they want to get out of it |
|---|---|---|
| 1 | **Vertt CTO** | Click through the customer flow, check trip data and settlement rules, decide the open topics. |
| 2 | **Innovation Booster partners** | Click through realistic bookings (travelcards, promo, payment methods, cancellation) and **collect the data** for their transaction layer. |
| (3) | Project team | Single reference for booking, trip and settlement data. |

Roles used in the user stories: Customer, Vertt, SBB, IB partner, Demo presenter.

## 3. Changes compared to the brief

| Topic | Brief | PRD |
|---|---|---|
| Interaction | Static page showing 3 trips | Clickable booking app (phone layout), steps 0–3 + receipt |
| Connections | One trip per route | Intermodal (bookable) + Vertt-only + public-transport-only (comparison) |
| SBB fare | Placeholder `null` | From OJP if available, otherwise public reference prices |
| Payment settlement | Out of scope | **Simulated** – B2B money movements generated as data |
| Edge cases | none | Travelcards (none / half-fare / GA), promo, cancellation of the whole journey |
| CO₂ | Car + rail factor | **Tailpipe only** → trains and electric cars = 0 kg |
| Output | Trip records | **Data link** per booking + **export of all bookings** |
| Hosting | local | Partners must open links → to decide with CTO |

Unchanged: no real payments or logins, no blockchain inside this prototype, privacy rules (brief section 8).

## 4. The customer flow

Phone layout (on a laptop: phone-sized in the middle). One neutral design for both apps – no official logos. Nothing has to be typed. 1 adult, 2nd class.

| Step | What happens | Stories |
|---|---|---|
| **0 – Choose app** | "Vertt app" or "SBB app". Decides who sells and collects the money. Fixed for the run. | 1a, 1b |
| **1 – Plan** *(most important)* | Start + destination (snapped to the nearest known place); time pre-filled and locked ("depart at"); travelcard (default half-fare) **or** "Log in with SwissPass" with test profile → travelcard locked. List of 3 connections with price and CO₂ per card; Vertt + SBB on top, "recommended – door to door with one booking". Details: legs, line, car category, transfers, map. | 2–11 |
| **2 – Log in** | Google / Apple / SwissPass / email + password (pre-filled, not editable) – one click. Skipped after SwissPass in step 1. | 12 |
| **3 – Overview & pay** | Map, legs, price per leg + total, CO₂, travelcard, "You pay [Vertt/SBB] for the whole journey". Promo tick 5 / 10 / 20 % on the Vertt part. Payment: card / TWINT / invoice / business (none pre-selected). No back button. | 13–15 |
| **Receipt** | Short payment animation → receipt for everyone. Buttons "Cancel journey" and "New booking". Data link "Settlement data (for project partners)" + copy; export of all bookings. | 16–18 |

## 5. User stories

21 agreed stories in 7 epics: see **[user-stories.md](user-stories.md)**.

## 6. Settlement rules

- The passenger pays **one** operator the full price: the **seller** = the app chosen in step 0.
- Rules are **fixed in the code**:

| Seller | Passenger pays | Settlement events |
|---|---|---|
| **Vertt app** | total → **Vertt** | Vertt → SBB: train ticket price · SBB → Vertt: **commission 5 % of the train ticket** (separate entry) |
| **SBB app** | total → **SBB** | SBB → Vertt: full Vertt part · **no commission** |

> **Deliberate demo decision:** the asymmetry (Vertt earns a commission, SBB does not) is chosen to show two different settlement rules in the data. It is **not** a business agreement with SBB.

Example (made-up numbers: Vertt ride CHF 30.00, train ticket CHF 8.40):

| Seller | Passenger pays | Events | Vertt ends with | SBB ends with |
|---|---|---|---|---|
| Vertt app | 38.40 → Vertt | Vertt → SBB 8.40; SBB → Vertt 0.42 | 30.42 | 7.98 |
| SBB app | 38.40 → SBB | SBB → Vertt 30.00 | 30.00 | 8.40 |

- Customer prices rounded to CHF 0.05; **B2B amounts exact to the centime**.
- Settled **per booking**.
- Vertt is **one party** – no driver share in the settlement.
- Amounts in CHF incl. VAT; VAT treatment of B2B transfers out of scope.

### Variations

| Case | Rule |
|---|---|
| Half-fare | Train ticket = half-fare price; commission (Vertt app) = 5 % of that |
| GA | Train ticket = CHF 0 → Vertt app: no transfer, no commission. SBB app: SBB passes the full Vertt part on and keeps CHF 0 |
| Promo (5/10/20 %) | Reduces only the Vertt part; carried by Vertt. SBB's share and commission unaffected |
| Cancel journey | Whole journey only. Full refund, no fee. New events: refund, reversal of B2B transfer, reversal of commission. Nothing is edited or deleted |
| Payment method | All count as paid immediately; no payment fees |

## 7. Output: data link and export

Each booking has one link (copy button) showing JSON:

1. **Booking** – `booking_id`, `system` (vertt / sbb), `login_method`, `travelcard`, `promo_percent`, `promo_chf`, `payment_method`, `booked_at`, `status`, pseudonymous demo customer ID.
2. **Trip** – legs with carrier, times, line / car category, car drawn from the pool (make, model, year, CO₂ factor), price, CO₂, data source of each value.
3. **Settlement events** – append-only list: `event_id, booking_id, seq, timestamp, event_type (b2c_payment | b2b_transfer | commission | refund | reversal), payer, payee, amount_chf, reason, refers_to_event`.

After a cancellation the **same link** shows the updated content. **Export** of all bookings since the page was first opened in this browser (across reloads, incl. cancellations) until "clear". Field names documented in `docs/schema.md`.

## 8. Not in scope (Prototype 1)

Real payments and logins, changeable time / "arrive by", more than 1 passenger, 1st class, settlement animation or operator dashboard, cancellation of a single leg, payment fees, business VAT receipt, blockchain integration, production hosting, delay / missed connection / no-show cases, official SBB or Vertt logos.

## 9. Open topics

All open topics and the technical API overview for the CTO meeting: **[cto-meeting.md](cto-meeting.md)**.

## 10. Definition of done

- A user can click through steps 0–3 and the receipt for every prepared route, both apps, all travelcards, with and without promo, all four payment methods.
- Cancellation works and updates the data link; export contains all bookings.
- Every number on screen is traceable to its source.
- Data links and export are valid JSON matching `docs/schema.md`.
- No personal data in the repo, on the page, in links or exports.
- The CTO has reviewed the demo and the open topics.

## 11. Next steps

1. CTO meeting: discuss [cto-meeting.md](cto-meeting.md), confirm this PRD.
2. Clickable mockup with fake data (optional, before the meeting).
3. Rework the GitHub issues to follow the user stories and the meeting decisions.
4. OJP API spike (station lookup, trip request, check for prices and platforms).
5. Build: data → settlement → booking interface → data link and export.
