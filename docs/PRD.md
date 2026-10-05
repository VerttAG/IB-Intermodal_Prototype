# PRD – Prototype 1: Intermodal Booking & Settlement Data Demo

| | |
|---|---|
| Status | **Draft v0.4** – partner APIs and a live trip engine decided by Tim (2026-10-05), see section 12; to be confirmed with Vertt CTO |
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
| Trips | 3 preset trips from recorded rides | **Calculated live** for any start/destination address and "depart at" time (section 12) |
| Connections | One trip per route | Up to 3 labelled trips (Fastest / Cheapest / Greenest, bookable) + Vertt-only + public-transport-only (comparison) |
| Vertt legs | Recorded rides | Calculated: Valhalla route × Vertt tariff, CO₂ with a car from the car pool. Recorded rides only validate the calculator |
| SBB fare | Placeholder `null` | From OJP Fare (beta) |
| Payment settlement | Out of scope | **Simulated** – B2B money movements generated as data |
| Edge cases | none | Travelcards (none / half-fare / GA), promo, cancellation of the whole journey |
| CO₂ | Car + rail factor | **Tailpipe only** → trains and electric cars = 0 kg |
| Output | Trip records | **Data link** per booking + **export of all bookings** |
| Hosting | local | Partners must open links → to decide with CTO |

Unchanged: no real payments or logins, no blockchain inside this prototype, privacy rules (brief section 8).

## 4. The customer flow

Phone layout (on a laptop: phone-sized in the middle). One neutral design for both apps – no official logos. Nothing has to be typed except the addresses (pre-filled with an example). 1 adult, 2nd class.

| Step | What happens | Stories |
|---|---|---|
| **0 – Choose app** | "Vertt app" or "SBB app". Decides who sells and collects the money. Fixed for the run. | 1a, 1b |
| **1 – Plan** *(most important)* | Start + destination address (swisstopo suggestions); "depart at" date and time; travelcard (default half-fare) **or** "Log in with SwissPass" with test profile → travelcard locked; "Search". Up to 3 trips labelled Fastest / Cheapest / Greenest ("door to door with one booking") + 2 comparison cards, each with price and CO₂. Details: legs (Vertt / walk / train), line, car category, waiting time, transfers, map. | 2–11, 27 |
| **2 – Log in** | Google / Apple / SwissPass / email + password (pre-filled, not editable) – one click. Skipped after SwissPass in step 1. | 12 |
| **3 – Overview & pay** | Map, legs, price per leg + total, CO₂, travelcard, "You pay [Vertt/SBB] for the whole journey". Promo tick 5 / 10 / 20 % on the Vertt part. Payment: card / TWINT / invoice / business (none pre-selected). No back button. | 13–15 |
| **Receipt** | Short payment animation → receipt for everyone. Buttons "Cancel journey" and "New booking". Data link "Settlement data (for project partners)" + copy; export of all bookings. | 16–18 |

## 5. User stories

Stories 1–21 (agreed v1) and 22–29 (v1.1, updated by Tim 2026-10-05) in **[user-stories.md](user-stories.md)**.

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
2. **Trip** – start and destination, legs (Vertt / walk / train) with carrier, times, line / car category, car drawn from the pool (make, model, year, CO₂ factor), price, CO₂, data source and assumptions of each value; OJP Fare details (product, net price, VAT rate); the trip's labels and the candidate stations with their origin (AI model / code fallback).
3. **Settlement events** – append-only list: `event_id, booking_id, seq, timestamp, event_type (b2c_payment | b2b_transfer | commission | refund | reversal), payer, payee, amount_chf, reason, refers_to_event`.

After a cancellation the **same link** shows the updated content. **Export** of all bookings since the page was first opened in this browser (across reloads, incl. cancellations) until "clear". Field names documented in `docs/schema.md`.

## 8. Not in scope (Prototype 1)

Real payments and logins, "arrive by", "use my location", peak-time factors and regional Vertt tariffs, booking or cancelling a ride through the Vertt API, more than 1 passenger, 1st class, settlement animation or operator dashboard, cancellation of a single leg, payment fees, business VAT receipt, blockchain integration, production hosting, delay / missed connection / no-show cases, official SBB or Vertt logos.

## 9. Open topics

All open topics and the technical API overview for the CTO meeting: **[cto-meeting.md](cto-meeting.md)**.

## 10. Definition of done

- A user can search any Swiss start and destination address with a chosen departure time and click through steps 0–3 and the receipt, in both apps, with all travelcards, with and without promo, all four payment methods.
- The demo gets Vertt data only through the Vertt API (documented in `docs/api/vertt.md`) and trips only through the middleware (`docs/api/trip-offers.md`).
- The calculator has been validated against the recorded rides, without anything that leads back to the passenger.
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

## 12. v0.4 – partner APIs and live trip engine

Proposed by Aleksandar, decided by Tim on 2026-10-05; to be confirmed with the CTO. Details in `specs/PROJ-1-intermodal-booking-demo/2_PRDs/` – mainly [PRD-9 trip engine](../specs/PROJ-1-intermodal-booking-demo/2_PRDs/PROJ-1-PRD-9-trip-engine.md), [PRD-7 Vertt API](../specs/PROJ-1-intermodal-booking-demo/2_PRDs/PROJ-1-PRD-7-vertt-partner-api.md), [PRD-8 middleware](../specs/PROJ-1-intermodal-booking-demo/2_PRDs/PROJ-1-PRD-8-trip-offer-middleware.md).

Both partners deliver their part of a journey through an interface. The booking demo is a **partner app** that only combines what the interfaces deliver.

| Partner | Interface | Delivers | Status |
|---|---|---|---|
| **SBB** | OJP 2.0 | Stations, train connections, walk legs, platforms, railway line, public-transport-only comparison | Exists – tested 2026-10-05 ([api/ojp20.md](api/ojp20.md)) |
| **SBB** | OJP Fare (beta) | Train price for no travelcard / half-fare, 2nd class | Exists – tested 2026-10-05 ([api/ojpfare.md](api/ojpfare.md)). GA not supported → demo rule CHF 0 |
| **Vertt** | **Vertt API (new)** | Ride offer for any two positions: distance, ride time, price (tariff), car from the pool, CO₂ factor, street route | **To build** – calculated with Valhalla + Vertt tariff |

```
Customer: start address, destination address, "depart at", travelcard
        │
        ▼
Middleware (our server) ── AI model Jev 1.13 (OpenRouter): chooses candidate stations
        │                   from a list of real stations (max. 3 per side)
        ├── Vertt API  (Valhalla × tariff, pool car)   ← first / last leg, or a walk
        ├── OJP 2.0    (first train ≥ 8 min after arrival at the station)
        └── OJP Fare   (prices for no travelcard + half-fare)
        │
        ▼
Totals per trip → labels Fastest / Cheapest / Greenest (calculated)
        │
        ▼
Booking demo: up to 3 labelled trips + "Vertt only" + "Public transport only"
```

- **No preset trips.** Every trip is calculated live; the 9 recorded rides only validate the calculator.
- **Trip shape:** Vertt ride or walk → station → train → station → Vertt ride or walk. Walk if the station is close enough, at both ends.
- **Vertt tariff:** Zurich values everywhere, factor 1.0 (assumption, to confirm with the CTO).
- **AI model:** chooses stations (a judgement), never the labels (a calculation). The search works without it (code fallback). It may receive the addresses – all trips are mock trips.
- **Server:** keys for OJP, OJP Fare, Vertt API and OpenRouter stay on the server → hosting (CTO topic T1); password gate in front of the demo (`mockup/middleware.js`).

What this settles from the CTO list: **T2** (Vertt legs calculated live), **B8** (SBB price from OJP Fare), GitHub issues #8, #9, #10, #11, #15.
