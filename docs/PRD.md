# PRD – Prototype 1: Intermodal Trip & B2B Settlement Demo

| | |
|---|---|
| Status | **Draft v0.1** – to be confirmed with Vertt CTO |
| Owner | Tim Diethelm (Vertt AG) |
| Last update | 2026-10-05 |
| Details | Technical details, data sources and calculations: [PROTOTYPE_1_BRIEF.md](PROTOTYPE_1_BRIEF.md). This PRD **extends** the brief; where they differ, this PRD wins. |

## 1. Why are we building this?

The Innovation Booster project aims at a settlement layer that bills and splits one intermodal journey (train + ride-hailing) between operators. Prototype 1 makes this tangible:

- It shows **what one intermodal trip looks like as data** (segments, times, route, fare, CO₂).
- It shows **how money moves between operators (B2B)** when the passenger pays only one of them.
- It produces **trip and settlement data** that the Innovation Booster partners use as input for their transaction layer (blockchain), and that Prototype 2 builds on.

The interesting part is the **B2B settlement**, not the B2C payment. The passenger payment is only a short animation.

## 2. Who uses it?

| Order | User | What they want to get out of it |
|---|---|---|
| 1 | **Vertt CTO** | Understand and challenge the trip data, the settlement model and the open decisions; decide on hosting and Vertt tariff input. |
| 2 | **Innovation Booster partners** | See a realistic booking flow and the money flows behind it; **download the settlement data** to feed their transaction layer. |
| (3) | Project team | Single reference for what the trip / settlement data looks like. |

## 3. Changes compared to the brief

| Topic | Brief | PRD |
|---|---|---|
| Payment settlement | Out of scope | **Core of the demo** – simulated, no real money |
| Interaction | Static page with 3 trips | Booking flow: choose start → choose end → see route, price, CO₂ → "pay" → see B2B money flows |
| Edge cases | none | Cancellation (full / one leg), GA, half-fare, promo |
| Output | Trip records | Trip records **+ settlement records** (transaction ledger), downloadable |
| Hosting | local | Partners need a URL → proposal: **GitHub Pages** (repo is public); confirm with CTO |

Unchanged: real data where possible (recorded Vertt rides, OJP timetable), no backend, no real payments, no blockchain inside this prototype, privacy rules (brief section 8).

## 4. The demo experience

1. **Choose start and end** from fixed lists (e.g. Wettswil am Albis, Mellingen Heitersberg, Winterthur, Ostermundigen). Only combinations with a prepared scenario can be selected.
2. **Choose the booking channel:** "Book in Vertt app" or "Book in SBB app".
3. Optionally choose **passenger options:** none / half-fare / GA; promo code yes/no.
4. **See the journey:** map with each leg (Vertt leg follows the real street route, train leg follows the track), timeline with transfer times, price per leg and total, CO₂ per leg and total. Constructed or placeholder values are visibly marked.
5. Click **"Pay for ride"** → short payment animation (B2C).
6. **Behind the scenes panel:** step-by-step animation of the B2B transactions – who collected the money, who owes whom, commission, final amount each operator keeps.
7. Optionally trigger an **edge case:** cancel the whole trip, or cancel one leg → see refunds and reversed B2B transactions.
8. **Download** the trip record and settlement records (JSON) of the current scenario, or all scenarios at once.

## 5. User stories

### Epic A – Journey
- **A1** As the **CTO**, I want to choose a start and an end and see the full journey on a map, so that I understand which leg is Vertt and which is SBB.
- **A2** As the **CTO**, I want to see departure/arrival times and transfer gaps on a timeline, so that I can judge if the connection is realistic (8–15 min window).
- **A3** As a **partner**, I want to see price and CO₂ per leg and per trip, so that I understand what each operator contributes.
- **A4** As **anyone**, I want constructed / placeholder values to be clearly marked, so that I don't mistake them for real data.

### Epic B – Settlement
- **B1** As the **CTO**, I want to switch between "booked in Vertt app" and "booked in SBB app", so that I see how the money flows differ.
- **B2** As a **partner**, I want to see each B2B transaction step by step (payer, payee, amount, reason), so that I understand what our transaction layer has to process.
- **B3** As the **CTO**, I want the commission rate to be a visible, adjustable assumption, so that we can discuss it with SBB.

### Epic C – Edge cases
- **C1** As a **partner**, I want to cancel a whole trip and see the refund and reversal transactions.
- **C2** As a **partner**, I want to cancel a single leg (e.g. train cancelled) and see which parts are refunded and which B2B transactions are reversed.
- **C3** As the **CTO**, I want to see how GA / half-fare change the SBB part and the B2B flows.
- **C4** As the **CTO**, I want to see who carries the cost of a promo discount.

### Epic D – Data
- **D1** As a **partner**, I want to download trip records and settlement records as JSON, so that I can feed them into our transaction layer.
- **D2** As the **project team**, I want the data format documented and stable, so that Prototype 2 can build on it.

## 6. Settlement model (draft)

- The passenger pays **one** operator in full: the **seller** (merchant of record) = the app they booked in.
- The seller passes on the other operator's share **minus a sales commission** (German: *Vertriebsprovision*).
- Commission rate: **configurable placeholder** (e.g. 5 %), open decision.
- Vertt is shown as **one party**; the internal split (driver earnings, service fee, VAT) stays in the data but not in the animation.
- All amounts in CHF incl. VAT. VAT treatment of B2B transfers is out of scope (noted as assumption).

Example (made-up numbers, ride CHF 30, train CHF 50, commission 5 %):

| Channel | Passenger pays | B2B transfer | Seller keeps | Other operator gets |
|---|---|---|---|---|
| Vertt app | 80 → Vertt | Vertt → SBB 47.50 | Vertt 32.50 | SBB 47.50 |
| SBB app | 80 → SBB | SBB → Vertt 28.50 | SBB 51.50 | Vertt 28.50 |

### Edge case rules (draft, all configurable)

| Case | Proposed default |
|---|---|
| Full cancellation before trip | Full refund by the seller; B2B transfer reversed; no fee (fee configurable) |
| One leg cancelled | That leg refunded by the seller; the matching B2B transfer and commission reversed; other leg stays paid |
| GA | SBB part = CHF 0 → no B2B transfer for SBB; if booked in SBB app, SBB still forwards the Vertt part minus commission |
| Half-fare | SBB part = 50 % of full fare |
| Promo | Discount carried by the operator who issued it (default: Vertt for Vertt promos) |

## 7. Data outputs

1. **Trip record** – schema v0 from the brief (section 6), plus `booking_channel` and passenger options.
2. **Settlement record** – an append-only list of events (ledger), one per money movement. Draft fields:
   `event_id, trip_id, scenario, seq, timestamp, event_type (b2c_payment | b2b_transfer | commission | refund | reversal), payer, payee, amount_chf, segment_seq, reason, data_basis`.
   An append-only event list is close to how a blockchain / transaction layer records entries, so partners can replay it directly.

Field names will be documented in `docs/schema.md` and kept stable.

## 8. Not in scope (Prototype 1)

Real payments, real bookings, live search for any address, blockchain integration, production hosting, delay / missed-connection / no-show / price-difference edge cases (candidates for Prototype 2).

## 9. Open decisions

Existing (brief section 7): GitHub issues #8–#16. New from this PRD:

| Topic | Default |
|---|---|
| Sales commission rate (Vertt ↔ SBB) | 5 % placeholder |
| Cancellation fee / refund policy | full refund, no fee |
| Who carries promo discounts | issuing operator |
| Settlement record format – align with partners' transaction layer | draft above |
| Hosting for partners (GitHub Pages?) | to decide with CTO |
| Demo date / audience meeting | not decided |

## 10. Definition of done

- A user can complete the flow in section 4 for all prepared scenarios, both channels, and all edge cases in section 6.
- Every number on screen is traceable to recorded data, timetable data or a marked assumption.
- Trip and settlement records download as JSON and validate against the documented schema.
- No personal data in the repo or on the page.
- The CTO has reviewed the demo and the open decisions.

## 11. Next steps

1. Review this PRD (Tim → CTO).
2. Clickable **mockup with fake data** to agree on the look and flow before real code.
3. Rework the GitHub issues to follow the epics above.
4. In parallel: **OJP API spike** (one real request) to remove the biggest technical risk.
5. Then build: data pipeline → settlement engine → interface.
