# PRD – Prototype 1: Intermodal Booking & Settlement Data Demo

| | |
|---|---|
| Status | **Draft v0.5** – decided by Tim 2026-10-05; to be confirmed with the Vertt CTO |
| Owner | Tim Diethelm (Vertt AG) · contributors: Aleksandar Bozic |
| Last update | 2026-10-05 |
| Details | Feature specs: [`specs/PROJ-1-intermodal-booking-demo/2_PRDs/`](../specs/PROJ-1-intermodal-booking-demo/2_PRDs/) (PRD-1 … PRD-8) · open points: [open-topics.md](open-topics.md) · API references: [`api/`](api/) |

## 1. Why are we building this?

The Innovation Booster project aims at a settlement layer that bills and splits one intermodal journey (train + ride-hailing) between operators. Prototype 1 makes this tangible:

- From the **customer's view**: a clickable booking app that builds a door-to-door journey for any two Swiss addresses – a Vertt ride to a station, the train, a Vertt ride to the destination – with times, price and CO₂ per carrier, similar to the SBB app.
- From the **settlement view**: every booking produces a **data link** with the money movements between the operators (B2B) and the CO₂. The Innovation Booster partners use this data as input for their transaction layer (blockchain); Prototype 2 builds on it.

The customer pays only **one** operator. The interesting part is the **B2B settlement** between the operators – it is captured in the data, not animated.

## 2. Who uses it?

| Order | User | What they want to get out of it |
|---|---|---|
| 1 | **Vertt CTO** | Click through the customer flow, check trip data and settlement rules, decide the open topics. |
| 2 | **Innovation Booster partners** | Click through realistic bookings (travelcards, promo, payment methods, cancellation) and **collect the data** for their transaction layer. |
| (3) | Project team | Single reference for booking, trip and settlement data. |

Roles in the stories: Customer, Vertt, SBB, IB partner, Demo presenter, Partner app.

## 3. How it works

```
Customer: start address, destination address, "depart at", travelcard → "Search"
        │
        ▼
Trip engine (our server on Vercel) – PRD-8
        ├── swisstopo        addresses → coordinates (under 10 km apart → "Trip not suitable for intermodal journey")
        ├── AI (Jev 1.13)    chooses max. 3 candidate stations per side from real OJP stations
        ├── Vertt API        first / last leg: Valhalla route × Vertt tariff, car from the car pool – PRD-7
        │                    (walk instead, if the station is within 1 km)
        ├── OJP 2.0          first train ≥ 8 min after arrival at the station, train CO₂ – PRD-6
        └── OJP Fare         half-fare price (no travelcard = × 2, GA = 0) – PRD-6
        │
        ▼
Totals per trip → labels Fastest / Cheapest / Greenest (calculated)
        │
        ▼
Booking app: up to 3 labelled trips + "Vertt only" + "Public transport only" (comparison)
```

- **No preset trips:** every trip is calculated live. The 9 recorded Vertt rides only **validate** the calculator.
- **Vertt tariff:** CHF 3.00 + 1.80/km + 0.30/min, minimum CHF 10.00, the same everywhere, factor 1.0.
- **AI:** chooses stations (a judgement), never the labels (a calculation). The search works without it.
- **Server:** keys for OJP, OJP Fare, Vertt API and OpenRouter stay on the server; a password gate protects the demo.

## 4. The customer flow

Phone layout (on a laptop: phone-sized in the middle). One neutral design for both apps – no official logos. Nothing has to be typed except the addresses. 1 adult, 2nd class.

| Step | What happens | Spec |
|---|---|---|
| **0 – Choose app** | "Vertt app" or "SBB app". Decides who sells and collects the money. Fixed for the run. | PRD-1 |
| **1 – Plan** *(most important)* | Start + destination address (swisstopo suggestions, empty at first); "depart at" date and time; travelcard (default half-fare) **or** "Log in with SwissPass" with test profile → travelcard locked; "Search". Up to 3 trips labelled Fastest / Cheapest / Greenest ("door to door with one booking") + 2 comparison cards, each with price and CO₂. Details: legs (Vertt / walk / train), line, car category, waiting time, transfers, map. | PRD-1, PRD-2 |
| **2 – Log in** | Google / Apple / SwissPass / email + password (pre-filled, not editable) – one click. Skipped after SwissPass in step 1. | PRD-3 |
| **3 – Overview & pay** | Map, legs, price per leg + total, CO₂, travelcard, "You pay [Vertt/SBB] for the whole journey". Promo tick 5 / 10 / 20 % on the Vertt part. Payment: card / TWINT / invoice / business (none pre-selected). No back button. | PRD-3 |
| **Receipt** | Short payment animation → receipt for everyone. Buttons "Cancel journey" and "New booking". Data link "Settlement data (for project partners)" + copy; export of all bookings. | PRD-3, PRD-4, PRD-5 |

## 5. User stories

The full stories with acceptance criteria are in the specs. Story numbers are used there in brackets.

| # | Story | Role | Priority | Spec |
|---|---|---|---|---|
| 1a | Choose the selling app (Vertt / SBB) | Demo presenter | Must | PRD-1 |
| 1b | Book the whole journey in my usual app | Customer | Must | PRD-3 |
| 2 | Enter start and destination address | Customer | Must | PRD-1 |
| 3 | Choose when to travel ("depart at") | Customer | Must | PRD-1 |
| 4 | State my travelcard | Customer | Must | PRD-1 |
| 5 | Log in with SwissPass while planning | Customer | Must | PRD-1 |
| 6 | See the labelled trips and comparisons | Customer | Must | PRD-2 |
| 7 | See the details of each leg | Customer | Must | PRD-2 |
| 8 | See price per leg and total | Customer | Must | PRD-2 |
| 9 | See CO₂ per leg and total | Customer | Must | PRD-2 |
| 10 | See the journey on a map | Customer | Must | PRD-2 |
| 11 | See what makes the offered trips special | Customer | Should | PRD-2 |
| 12 | Log in with an existing account | Customer | Must | PRD-3 |
| 13 | See an overview before paying | Customer | Must | PRD-3 |
| 14 | Apply a promo code | Customer | Must | PRD-3 |
| 15 | Choose a payment method | Customer | Must | PRD-3 |
| 16 | Pay and get a receipt | Customer | Must | PRD-3 |
| 17 | Get the booking data (data link, export) | IB partner | Must | PRD-5 |
| 18 | Cancel the journey | Customer | Must | PRD-4 |
| 19 | Vertt sells the journey (5 % commission) | Vertt | Must | PRD-4 |
| 20 | SBB sells the journey (no commission) | SBB | Must | PRD-4 |
| 21 | No personal data anywhere | Vertt | Must | PRD-5, PRD-7 |
| 22 | Train connections from the official journey planner | SBB | Must | PRD-6 |
| 23 | Train prices from the official price interface | SBB | Must | PRD-6 |
| 24 | Vertt rides through a Vertt API | Vertt | Must | PRD-7 |
| 25 | A documented, stable Vertt API | IB partner | Must | PRD-7 |
| 26 | A calculator Vertt can trust (validation) | Vertt | Must | PRD-7 |
| 27 | Fastest, cheapest, greenest | Customer | Must | PRD-8 |
| 28 | One service for complete trip offers | Partner app | Must | PRD-8 |
| 29 | The AI chooses the stations worth trying | Demo presenter | Must | PRD-8 |

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

- Customer prices rounded to CHF 0.05; the settlement starts from these rounded amounts. **B2B amounts exact to the centime**; the commission is rounded half up.
- Settled **per booking**. Vertt is **one party** – no driver share.
- Amounts in CHF incl. VAT; VAT treatment of B2B transfers out of scope.

| Case | Rule |
|---|---|
| Half-fare | Train ticket = half-fare price; commission (Vertt app) = 5 % of that |
| No travelcard | Train ticket = 2 × half-fare price |
| GA | Train ticket = CHF 0 → Vertt app: no transfer, no commission. SBB app: SBB passes the full Vertt part on and keeps CHF 0 |
| Promo (5/10/20 %) | Reduces only the Vertt part; carried by Vertt. SBB's share and commission unaffected |
| Cancel journey | Whole journey only, only from the receipt. Full refund, no fee. New events: refund, reversal of B2B transfer, reversal of commission. Nothing is edited or deleted |
| Payment | All methods count as paid immediately; no payment fees. A booking exists from the click on "Pay" |

## 7. Output: data link and export

Each booking has one link (copy button) showing JSON – **transactional data only**:

1. **Booking** – `booking_id`, `system` (vertt / sbb), `login_method`, `travelcard`, `promo_percent`, `promo_chf`, `payment_method`, `booked_at`, `status`, pseudonymous demo customer ID.
2. **Amounts per leg** – operator (Vertt / SBB), type (Vertt ride / train), amount in CHF, CO₂ in kg, plus the trip's total CO₂. **No** addresses, coordinates, stations, times, car or labels.
3. **Settlement events** – append-only list: `event_id, booking_id, seq, timestamp, event_type (b2c_payment | b2b_transfer | commission | refund | reversal), payer, payee, amount_chf, reason, refers_to_event`.

The data is stored online on **Vercel**; after a cancellation the **same link** shows the updated content. **Export** of all bookings since the page was first opened in this browser (across reloads, incl. cancellations) until "Clear" – which empties only the local list; links already sent keep working. Field names documented in `docs/schema.md` (to be written).

## 8. Not in scope (Prototype 1)

Real payments and logins, "arrive by", "use my location", peak-time factors, booking or cancelling a ride through the Vertt API, more than 1 passenger, 1st class, settlement animation or operator dashboard, cancellation of a single leg or after leaving the receipt, payment fees, business VAT receipt, blockchain integration, production hosting, delay / missed connection / no-show cases, official SBB or Vertt logos.

## 9. Definition of done

- A user can search any Swiss start and destination address (10 km or more apart) with a chosen departure time and click through steps 0–3 and the receipt, in both apps, with all travelcards, with and without promo, all four payment methods.
- The demo gets Vertt data only through the Vertt API (`docs/api/vertt.md`) and trips only through the trip engine (`docs/api/trip-offers.md`).
- The calculator has been validated against the recorded rides, without anything that leads back to the passenger.
- Cancellation works and updates the data link; export contains all bookings.
- Data links and export are valid JSON matching `docs/schema.md`.
- No personal data in the repo, on the page, in links or exports.
- The CTO has reviewed the demo and the open topics.

## 10. Next steps

1. CTO meeting: go through [open-topics.md](open-topics.md), confirm this PRD.
2. Spike: AI station choice on 5–10 example journeys (PRD-8).
3. Car pool (`config/car_pool.yaml`) and validation of the calculator against the recorded rides (PRD-7).
4. Create the build tasks as GitHub issues from the specs.
5. Build: Vertt API → trip engine → booking app → settlement, data link and export.
