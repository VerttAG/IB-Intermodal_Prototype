# PRD – Prototype 1: Intermodal Booking & Settlement Data Demo

| | |
|---|---|
| Status | **Draft v0.2** – to be confirmed with Vertt CTO |
| Owner | Tim Diethelm (Vertt AG) |
| Last update | 2026-10-05 |
| Details | Technical details, data sources and calculations: [PROTOTYPE_1_BRIEF.md](PROTOTYPE_1_BRIEF.md). This PRD **extends** the brief; where they differ, this PRD wins. |

## 1. Why are we building this?

The Innovation Booster project aims at a settlement layer that bills and splits one intermodal journey (train + ride-hailing) between operators. Prototype 1 makes this tangible:

- From the **customer's view**: a clickable booking app that shows one door-to-door journey combining Vertt and SBB – route, times, price and CO₂ per carrier – similar to the SBB app.
- From the **settlement view**: every booking produces a **data link** with the full trip and all B2B transactions (who owes whom). The Innovation Booster partners use this data as input for their transaction layer (blockchain), and Prototype 2 builds on it.

The customer pays only **one** operator. The interesting part is the **B2B settlement** between the operators, which is captured in the data, not shown as an animation.

## 2. Who uses it?

| Order | User | What they want to get out of it |
|---|---|---|
| 1 | **Vertt CTO** | Click through the customer flow, check that the trip data and settlement rules are right, decide on the open points. |
| 2 | **Innovation Booster partners** | Click through realistic bookings (incl. travelcards, payment methods, cancellations) and **collect the generated data links** to feed their transaction layer. |
| (3) | Project team | Single reference for what booking, trip and settlement data look like. |

## 3. Changes compared to the brief

| Topic | Brief | PRD |
|---|---|---|
| Interaction | Static page showing 3 trips | Clickable booking app (phone layout) with 4 steps (section 4) |
| Connections | One trip per route | Per route: intermodal trip (recommended) + Vertt-only + public-transport-only alternative |
| SBB fare | Placeholder `null` | From OJP if available, otherwise public reference prices (marked) |
| Payment settlement | Out of scope | **Simulated** – B2B transactions generated as data (no real money, no animation) |
| Edge cases | none | Travelcards (none / half-fare / GA), promo code, cancellation (whole trip / one leg) |
| Output | Trip records | **Data link** per booking: booking + trip record + settlement events (JSON) |
| Hosting | local | Partners must open the links → proposal: **GitHub Pages** (repo is public); confirm with CTO |

Unchanged: real data where possible (recorded Vertt rides, OJP timetable), no backend, no real payments or logins, no blockchain inside this prototype, privacy rules (brief section 8).

## 4. The customer flow

One neutral design for both systems; only a label shows which operator's app is used. Phone layout (on a laptop: phone-sized screen in the middle). Nothing has to be typed – everything is clickable.

### Step 0 – Choose system
"Vertt app" or "SBB app". This decides who sells the trip and collects the money (the **seller**, see section 6).

### Step 1 – Route and travelcard  *(most important screen)*
- **From / To:** chosen from fixed lists (e.g. Wettswil am Albis, Winterthur, Mellingen Heitersberg, Ostermundigen). Only combinations with a prepared scenario can be chosen.
- **Date / time:** shown like in the SBB app, pre-filled with the scenario time, not changeable.
- **Travelcard:** quick choice *no travelcard / half-fare / GA*.
- **"Log in with SwissPass"** button as alternative: after the click, a small box below lets the user pick the test profile *no travelcard / half-fare / GA*. Step 2 is then skipped.
- **Connection list**, styled like the SBB app:
  1. **Intermodal trip (Vertt + SBB)** – on top, marked as recommended. Built from the real recorded Vertt ride(s) and the OJP train leg.
  2. **Vertt only** – car the whole way. Constructed (marked).
  3. **Public transport only** – from OJP (e.g. bus + train), real timetable data.
- Each connection shows per leg: carrier (Vertt / SBB and line, e.g. S11, IC 8), departure and arrival time, duration, transfer time, **price** and **CO₂**; plus totals. Constructed or reference values are visibly marked.
- Opening a connection shows the **map** (Vertt leg along the real street route, train leg along the track) and the detailed timeline.

### Step 2 – Log in
One click on **Google**, **Apple** or **SwissPass** (fake, no data entered). Skipped if SwissPass was used in step 1.

### Step 3 – Overview and payment
- Route again with map, price per carrier and total, CO₂ per leg and total.
- Optional **promo code** field.
- Payment method: **card**, **TWINT**, **invoice** (private), or **business** (invoice to company + receipt with VAT shown). All fake, one click.
- **"Pay"** → short confirmation.

### After payment – Data link and cancellation
- A **link** is generated with all data of this booking (section 7), with a **copy** button. Opening it shows the JSON in the browser.
- **Cancel** buttons: *cancel whole trip* or *cancel one leg* → generates a **new link** containing the original events plus the refund / reversal events.

## 5. User stories

### Epic A – Choose and compare (step 0 + 1)
- **A1** As a **customer**, I want to choose whether I book in the Vertt or the SBB app, so that I use the app I'm used to.
- **A2** As a **customer**, I want to choose start and destination and see my connections, so that I can decide how to travel.
- **A3** As a **customer**, I want to see each leg with carrier, times, price and CO₂ like in the SBB app, so that I understand what I'm buying.
- **A4** As a **customer**, I want to compare the intermodal trip with Vertt-only and public-transport-only, so that I see why the combination is recommended.
- **A5** As a **customer**, I want to see the trip on a map, so that I see where the car drives and where I take the train.
- **A6** As a **customer**, I want to state my travelcard (or log in with SwissPass), so that I see my real price.
- **A7** As the **CTO**, I want every constructed or reference value marked, so that nobody mistakes it for real data.

### Epic B – Log in and pay (step 2 + 3)
- **B1** As a **customer**, I want to log in with one click (Google / Apple / SwissPass), so that booking is fast.
- **B2** As a **customer**, I want to see a final overview with map, price and CO₂ before paying.
- **B3** As a **customer**, I want to pay by card, TWINT, invoice or as a business with receipt, so that I can pay the way I need.
- **B4** As a **customer**, I want to enter a promo code, so that I get my discount.

### Epic C – Settlement data
- **C1** As a **partner**, I want a link with all booking, trip and settlement data after each payment, so that I can feed it into our transaction layer.
- **C2** As a **partner**, I want each B2B transaction listed with payer, payee, amount and reason, so that our layer can process it.
- **C3** As a **partner**, I want cancellation (whole trip / one leg) to produce refund and reversal events, so that we can test reversals.
- **C4** As the **project team**, I want the data format documented and stable, so that Prototype 2 can build on it.

## 6. Settlement rules

- The passenger pays **one** operator the full price: the **seller** = the app chosen in step 0.
- The seller forwards the other operator's share. Rules are **fixed in the code** (not configurable) to show two different cases:

| Seller | Passenger pays | B2B transfer | Commission |
|---|---|---|---|
| **Vertt app** | Vertt part + train ticket → **Vertt** | Vertt → SBB: train ticket **− 5 %** | Vertt keeps **5 % of the train ticket** |
| **SBB app** | Vertt part + train ticket → **SBB** | SBB → Vertt: **full** Vertt part | none |

Example (made-up numbers: Vertt ride CHF 30, train ticket CHF 50):

| Seller | Passenger pays | B2B transfer | Vertt ends with | SBB ends with |
|---|---|---|---|---|
| Vertt app | 80 → Vertt | Vertt → SBB 47.50 | 32.50 | 47.50 |
| SBB app | 80 → SBB | SBB → Vertt 30.00 | 30.00 | 50.00 |

- Vertt is **one party**; its internal split (driver earnings, service fee, VAT) stays in the data but is not part of the B2B transactions.
- All amounts in CHF incl. VAT. VAT treatment of B2B transfers is out of scope (assumption).

### Edge cases

| Case | Rule |
|---|---|
| **Half-fare** | Train ticket = half-fare price; Vertt commission = 5 % of that price |
| **GA** | Train ticket = CHF 0 → no transfer to SBB and no commission (Vertt app); SBB app still forwards the full Vertt part |
| **Promo code** | Discount on the Vertt part, carried by Vertt (issuer). Passenger pays less; if sold by SBB, SBB forwards the discounted Vertt part |
| **Cancel whole trip** | Seller refunds the passenger in full; all B2B transfers reversed (incl. commission) |
| **Cancel one leg** | Seller refunds that leg; the matching B2B transfer (and commission, if any) reversed; the other leg stays paid |
| **Invoice / business payment** | Treated as paid at booking (simplification); payment method recorded in the data |

## 7. Data link (output)

Each booking produces one JSON document, reachable via the link:

1. **Booking** – `booking_id`, `system` (vertt / sbb), `login_method`, `travelcard`, `promo_code`, `payment_method`, `booked_at`. Customer is a pseudonymous demo ID – no personal data.
2. **Trip record** – schema v0 from the brief (section 6), incl. segments, `data_basis` flags, fares and CO₂.
3. **Settlement events** – append-only list, one entry per money movement:
   `event_id, booking_id, seq, timestamp, event_type (b2c_payment | b2b_transfer | commission | refund | reversal), payer, payee, amount_chf, segment_seq, reason, refers_to_event`.
   An append-only event list is close to how a blockchain / transaction layer records entries, so partners can replay it directly. A cancellation adds new events; it never edits old ones.

Field names will be documented in `docs/schema.md` and kept stable.

## 8. Not in scope (Prototype 1)

Real payments and logins, live search for any address or time, settlement animation or operator dashboard, blockchain integration, production hosting, delay / missed connection / no-show / price-difference cases (candidates for Prototype 2), official SBB or Vertt logos.

## 9. Open decisions

Existing (brief section 7): GitHub issues #8–#16. New from this PRD:

| Topic | Default |
|---|---|
| Can OJP deliver SBB prices? (brief says OJP 2.0 has no fares) | check in OJP spike; else public reference prices |
| Vertt-only alternative: price and CO₂ without a tariff formula | constructed estimate, marked |
| Is only the intermodal connection bookable, or all three? | only intermodal is bookable; others for comparison |
| Cancellation fee / refund policy | full refund, no fee |
| VAT rate shown on business receipt | 8.1 % (to verify) |
| Settlement data format – align with partners' transaction layer | draft in section 7 |
| Hosting for partners (GitHub Pages?) | to decide with CTO |
| Demo date / audience meeting | not decided |

## 10. Definition of done

- A user can click through steps 0–3 for every prepared route, both systems, all travelcards, with and without promo, all four payment methods.
- Cancellation of the whole trip and of one leg works and produces a new data link.
- Every number on screen is traceable to recorded data, timetable data or a marked assumption.
- Data links contain valid JSON that matches the documented schema.
- No personal data in the repo, on the page or in the links.
- The CTO has reviewed the demo and the open decisions.

## 11. Next steps

1. Review this PRD (Tim → CTO).
2. Clickable **mockup with fake data** of steps 0–3, to agree on look and flow before real code.
3. Rework the GitHub issues to follow the epics above.
4. In parallel: **OJP API spike** – one real station lookup + trip request, and check whether prices are returned.
5. Then build: data pipeline → settlement engine → booking interface → data link.
