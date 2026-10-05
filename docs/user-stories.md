# User Stories – Prototype 1

Status: **v1** – discussed and agreed by Tim, 2026-10-05. Input for the CTO meeting.
Context: [PRD.md](PRD.md). Technical questions and open topics: [cto-meeting.md](cto-meeting.md).

**How to read this**
- Each story describes a **real need** (who, what, why). The **acceptance criteria** describe what **Prototype 1** does – demo limitations are stated there, not in the story.
- Stories say nothing about the engine or APIs behind them on purpose.
- Priority (MoSCoW): **Must** = needed for the demo, **Should** = important but demo works without, **Could** = nice to have.

**Roles**

| Role | Who |
|---|---|
| Customer | Private person booking a door-to-door journey |
| Vertt | Vertt as operator (business / finance side) |
| SBB | SBB as operator (business / finance side) |
| IB partner | Innovation Booster partners building the transaction layer |
| Demo presenter | Tim / CTO showing the demo |

**General demo rules** (apply to all stories)
- Phone layout, one neutral design for both apps. Only step 0 differs.
- Nothing has to be typed – everything is clickable.
- 1 adult, 2nd class. Customer prices rounded to CHF 0.05.
- A run starts with step 0 and ends with "pay" (or a reload). Choices made in a run (app, login) cannot be undone within the run.

---

## E0 – Choose app

### 1a · Choose the selling app *(Demo presenter · Must)*
> As a demo presenter, I want to choose whether the booking happens in the Vertt app or in the SBB app, so that I can show how the settlement changes depending on who sells the trip.

- Two options: "Vertt app" and "SBB app".
- Every following screen shows which app is being used.
- The choice is fixed for the run; only "pay" (end of run) or a reload starts over.

### 1b · Book everything in my usual app *(Customer · Must)*
> As a customer, I want to book my whole door-to-door journey in the app I already use, so that I don't have to switch between apps.

- All legs (Vertt and SBB) are booked in one flow with one payment, in either app.

---

## E1 – Plan the journey  *(most important epic)*

### 2 · Choose start and destination *(Customer · Must)*
> As a customer, I want to set where my journey starts and where it ends, so that I get a door-to-door connection and not just station to station.

- Start and destination can be set, including places that are not stations.
- If the input is not one of the known places, the demo uses the **nearest known place** and says so clearly ("We use X, 2.1 km from your address").
- If the nearest known place is too far away, a clear message says the area is not covered.
- If there is no connection for a combination, a clear message says so.
- No swap button.

### 3 · Choose when to travel *(Customer · Must)*
> As a customer, I want to choose when I want to travel, so that I get connections that fit my plans.

- Date and time are shown as **"depart at"**, like in a normal journey planner.
- In Prototype 1 the time is **pre-filled** with the scenario time and **locked** (lock icon, hint "fixed in demo").

### 4 · State my travelcard *(Customer · Must)*
> As a customer, I want to state which travelcard I have, so that I see the price I actually have to pay.

- Options: no travelcard, half-fare, GA. **Default: half-fare.**
- Changing the travelcard updates all prices immediately.
- The travelcard only affects the SBB part; the Vertt part stays the same.
- The travelcard is shown again in the overview and stored in the data link.

### 5 · Log in with SwissPass *(Customer · Must)*
> As a customer with a SwissPass, I want to log in with my SwissPass while planning, so that my travelcard is filled in automatically and I don't have to log in again before paying.

- Step 1 has a "Log in with SwissPass" button (in both apps).
- After the click, a small box offers three test profiles: no travelcard / half-fare / GA.
- The chosen profile fills in the travelcard and **locks** it ("from SwissPass").
- No log-out within the run.
- Step 2 is skipped.
- The data link stores `login_method = swisspass` and the travelcard.

### 6 · See a list of connections *(Customer · Must)*
> As a customer, I want to see several ways to make my journey side by side, so that I can choose the one that suits me best.

- Three connections: **Vertt + SBB (+ Vertt)** on top, **Vertt only**, **public transport only**.
- Each card shows departure, arrival, duration, number of transfers, transport mode icons, **total price and total CO₂**.
- Only the Vertt + SBB connection is bookable; the others are marked "for comparison" and have no book button.
- Tapping a card opens the details (story 7).
- If a connection type doesn't exist for a route, it is not shown, or a note explains why.

### 7 · See the details of each leg *(Customer · Must)*
> As a customer, I want to see every leg of my journey in detail, so that I know exactly what happens and where I need to be.

- Each leg: carrier, mode icon, from → to, departure, arrival, duration.
- Train legs: line (e.g. S11, IC 8).
- Vertt legs: car **category** (Prototype 1: only "Vertt"; later e.g. "Premium").
- The Vertt car is drawn at random from a pool **once per run**, stays the same until the end of the run, and is stored in the data link (it determines CO₂).
- Between legs: a transfer row with the minutes available.
- *(Could)* Warning if a transfer is outside the 8–15 min window ("tight" / "long wait").
- *(Could)* Platform for train legs, if available.

### 8 · See price per leg and in total *(Customer · Must)*
> As a customer, I want to see what each leg costs and what I pay in total, so that I understand what I pay for and can compare connections.

- Each leg shows its price in CHF; the total is shown clearly. **Split per leg is visible.**
- Total = sum of the (rounded) legs; no hidden fees. Rounding to CHF 0.05.
- With half-fare / GA the train part shows a hint ("half-fare price" / "covered by GA", CHF 0.00).
- The comparison connections also show a price.

### 9 · See CO₂ per leg and in total *(Customer · Must)*
> As a customer, I want to see how much CO₂ each leg and the whole journey cause, so that I can choose a more climate-friendly connection.

- CO₂ in **kg with 1 decimal**, per person, per leg and total.
- Method: **tailpipe only** (tank-to-wheel) → electric trains and electric cars = 0.0 kg.
- The Vertt leg's CO₂ depends on the car drawn for the run.
- Missing values show "not available", never 0.
- No comparison hint ("saves X kg").

### 10 · See the journey on a map *(Customer · Must)*
> As a customer, I want to see my whole journey on a map, so that I understand where the car takes me, where I change and where the train goes.

- Map only for the bookable connection; shown in the connection details and in the overview (step 3).
- Each leg coloured by carrier, with legend.
- Vertt legs follow the streets, train legs follow the railway line (straight lines only if no geometry is available, then marked).
- Markers for start, transfer point(s) and destination – showing the **known place**, not the typed address.
- Map zooms to show the whole journey. No highlighting of legs.

### 11 · See why a connection is recommended *(Customer · Should)*
> As a customer, I want to see what makes the recommended connection special, so that I understand the benefit of booking Vertt and SBB together.

- The Vertt + SBB connection is labelled "recommended" with the fixed reason **"Door to door with one booking"**.

---

## E2 – Log in

### 12 · Log in with an existing account *(Customer · Must)*
> As a customer, I want to log in with an account I already have, so that I can book without creating a new account.

- Four options: Google, Apple, SwissPass, email + password. Each logs in with one click.
- Email + password fields are pre-filled with demo values and cannot be edited.
- Step 2 is skipped if SwissPass was already used in step 1.
- SwissPass in step 2 does **not** change the travelcard chosen in step 1.
- The data link stores `login_method` and a pseudonymous demo customer ID.

---

## E3 – Overview and payment

### 13 · See an overview before paying *(Customer · Must)*
> As a customer, I want to see everything I'm about to book on one screen before I pay, so that I can check it and am not surprised later.

- Shows the **map**, start → destination, date/time, all legs with carrier and times, price per leg and total, CO₂ per leg and total, travelcard.
- Shows clearly: **"You pay [Vertt / SBB] for the whole journey."**
- No back button.

### 14 · Apply a promo code *(Customer · Must)*
> As a customer, I want to apply a promo code before paying, so that I get the discount I was promised.

- A "promo code" area with three options to tick: **5 %, 10 %, 20 %** on the Vertt part. At most one; the tick can be removed.
- The discount reduces only the Vertt part (visible, e.g. "CHF 23.90 → CHF 21.50"); total updates, rounded to CHF 0.05.
- Works the same in both apps.
- The data link stores percentage, discount in CHF, and that **Vertt** carries it.

### 15 · Choose a payment method *(Customer · Must)*
> As a customer, I want to pay the way I'm used to, so that booking fits my habits and my situation.

- Options: card, TWINT, invoice, business. **None pre-selected**; one must be chosen before "pay" is enabled.
- No input fields for payment data.
- All methods count as **paid immediately**; no payment fees.
- The data link stores `payment_method`.

### 16 · Pay and get a receipt *(Customer · Must)*
> As a customer, I want to pay with one click and immediately see a receipt, so that I know my booking is confirmed and what I paid for.

- After "pay": short payment animation, then the receipt.
- Receipt (for **every** payment method): booking number, seller, date, start → destination, each leg with carrier and price, discount, total, travelcard, payment method.
- Receipt has the buttons **"Cancel journey"** and **"New booking"**, and the data link (story 17).

---

## E4 – After booking

### 17 · Get the booking data *(IB partner · Must)*
> As an IB partner, I want a link to the complete data of each booking, so that I can feed real-looking bookings into our transaction layer and test it.

- The receipt shows a link "Settlement data (for project partners)" with a copy button.
- Opening it shows the booking as JSON: booking details, trip with all legs, settlement events (money movements).
- After a cancellation, the **same link** shows the updated content.
- **Export of all bookings** as one file: all bookings since the page was first opened in this browser, across reloads, including cancellations, until "clear" is clicked.
- No personal data; field names documented in `docs/schema.md` and kept stable.

### 18 · Cancel the journey *(Customer · Must)*
> As a customer, I want to cancel my booked journey, so that I get my money back if my plans change.

- "Cancel journey" → confirmation "Really cancel?" → receipt marked **"Cancelled"** with refund amount.
- Only the **whole journey** can be cancelled, only once.
- Full refund, no fee.
- Settlement events are only **added**, never changed: refund to customer, reversal of the B2B transfer, reversal of the commission.
- "New booking" starts a new run (like a reload); the export keeps all bookings.

---

## E5 – Settlement between operators

General: B2B amounts are calculated **exactly to the centime**, settled **per booking**. Vertt is one party (no driver share).

### 19 · Vertt sells the journey *(Vertt · Must)*
> As Vertt, when a customer books the whole journey in my app, I want to collect the full price and pass SBB's share on minus a 5 % commission, so that I'm rewarded for selling SBB tickets and SBB still gets its money.

- Customer pays the full total (after travelcard and promo) → Vertt.
- Settlement events: "Vertt → SBB: train ticket price" **and** a separate entry "SBB → Vertt: commission 5 % of the train ticket".
- Half-fare: commission on the half-fare price. GA: no transfer, no commission.
- Promo reduces only the Vertt part; SBB's share and the commission are unaffected.
- Cancellation reverses transfer and commission.

### 20 · SBB sells the journey *(SBB · Must)*
> As SBB, when a customer books the whole journey in my app, I want to collect the full price and pass Vertt's full share on, so that Vertt is paid for its rides and my customers can travel door to door with one booking.

- Customer pays the full total (after travelcard and promo) → SBB.
- Settlement event: "SBB → Vertt: Vertt part" (full, after promo). **No commission** – a deliberate demo decision (see PRD).
- Half-fare / GA change only the SBB part. With GA, SBB keeps CHF 0 and passes everything on.
- Cancellation reverses the transfer.

---

## E6 – Trust and data quality

### 21 · No personal data anywhere *(Vertt · Must)*
> As Vertt, I want the demo, the code and the data links to contain no personal customer data, so that we comply with data protection (nDSG) and can share everything freely with the partners – the repo is public.

- No names, emails, home addresses or real passenger IDs in the repo, on the page, in data links or in the export.
- Known places are localities or stations only.
- Addresses typed by the customer are not stored or passed on.
- Customer ID = pseudonymous demo ID.
- The car pool contains make, model, year and CO₂ only – no number plates.

> Marking of real vs. estimated values was discussed as a story and moved to the CTO meeting as a discussion topic (see [cto-meeting.md](cto-meeting.md)).

---

# v1.1 – proposed additions (not yet agreed)

> **Decision by Tim, 2026-10-05 – trip engine ([PROJ-1-PRD-9](../specs/PROJ-1-intermodal-booking-demo/2_PRDs/PROJ-1-PRD-9-trip-engine.md)):** stories 22, 23, 25, 26, 27 and 28 are accepted with these changes: trips are **calculated live** for any address and a chosen "depart at" time (no preset trips); the Vertt API (24) **calculates** offers with Valhalla + tariff + a car from the car pool, and the recorded rides serve only to validate the calculator. Story 29 changes: the AI model **proposes candidate stations** (max. 3 per side, checked against OJP); the labels Fastest / Cheapest / Greenest are **calculated**, not chosen by the model. The change table at the end of this section is updated by PRD-9 ("Changes to other specs").

Added 2026-10-05. Reason: the data of both partners comes through an interface – **SBB through OJP 2.0 and OJP Fare**, **Vertt through its own API** built from the recorded rides Vertt provided. The Vertt API is reused in the later prototypes. Stories 1–21 above are unchanged; the table at the end lists what the new stories change in them.
On top of the two interfaces sits a **middleware of our own** that builds whole trips from the partners' leg offers and lets an **AI model** (Jev 1.13 via OpenRouter) label the fastest, cheapest and greenest one (stories 27–29).
Detailed requirements: `specs/PROJ-1-intermodal-booking-demo/2_PRDs/` (PRD-6 for SBB, PRD-7 for Vertt, PRD-8 for the middleware).

New role: **Partner app** – any app that plans and sells a journey with another operator's legs (in Prototype 1: the booking demo itself).

## E7 – Partner data

### 22 · Train connections from the official journey planner *(SBB · Must)*
> As SBB, I want the train legs of the demo to come from the official journey planner, so that the times, lines and platforms the customer sees are real.

- Stations, train legs, transfer times and the railway line on the map come from **OJP 2.0**.
- The public-transport-only comparison (story 6) is also an OJP connection.
- Times are shown in Swiss local time.
- After a Vertt leg, the train is the first one leaving at least 8 minutes after the Vertt arrival.
- If OJP gives no answer, nothing is made up: the connection is not offered, or a stored earlier answer is used and marked.

### 23 · Train prices from the official price interface *(SBB · Must)*
> As SBB, I want the train price in the demo to come from the official price interface, so that the customer and the partners see a real price.

- Price for 1 adult, 2nd class from **OJP Fare (beta)**, for "no travelcard" and "half-fare".
- GA = CHF 0.00 by the demo's own rule (OJP Fare does not know GA).
- The price is marked "OJP Fare (beta)"; product name, price without VAT and VAT rate are stored in the data link.
- The price shown in the overview is the price paid; a booking keeps its price even if OJP Fare changes it later (saver prices).
- A missing price shows "not available", never CHF 0.00, and the connection cannot be booked.

### 24 · Vertt rides through a Vertt API *(Vertt · Must)*
> As Vertt, I want to offer my rides through an interface of my own, like SBB does, so that a partner app can plan and price a Vertt leg without knowing how Vertt works inside.

- The API answers two questions: **which places** does Vertt serve, and **what does a ride** from A to B look like (distance, duration, price, car, CO₂ factor, route for the map).
- It is built from the recorded rides Vertt provided: every offer is backed by a real ride on that route.
- Price = the full ride price, without tip and without a discount given in the past. Promo codes stay in the booking app (story 14).
- An offer has no clock time; the booking app places the ride before or after the train.
- For a route without a recorded ride the answer is "not served". Estimated offers are only allowed if clearly marked.
- The booking demo gets its Vertt data only through this API.

### 25 · A documented, stable Vertt API *(IB partner · Must)*
> As an IB partner, I want the Vertt API to be documented and stable, so that we can build on it in the later prototypes.

- `docs/api/vertt.md` describes every request and field with an example, next to the OJP documents.
- Answers are JSON and carry a version; field names do not change silently.
- Read-only in Prototype 1: no booking or cancelling of rides through the API.
- Access (decided 2026-10-05): in Prototype 1 only our own app can call the API; partners get the description, and access with a key of their own later.

### 26 · No trace of the passenger in the Vertt API *(Vertt · Must)*
> As Vertt, I want the API to give away nothing about the passenger behind the recorded rides, so that we can run it openly and share it with partners.

- All provided rides belong to **one** passenger and start or end at a home address.
- No passenger ID, vehicle ID, address, street or postcode in any answer.
- The route on the map does not start or end at the house: the part near the home is cut off or moved to the locality.
- No original date, clock time or ride ID of a recorded ride.
- The Excel export is never committed, hosted or reachable; the API works from cleaned data only.

## E8 – Trip offers

### 27 · Fastest, cheapest, greenest *(Customer · Must)*
> As a customer, I want to see the fastest, the cheapest and the greenest way to make my journey, so that I can pick by what matters to me.

- The Vertt + SBB connections are shown as up to three trip offers with the labels **"Fastest"**, **"Cheapest"**, **"Greenest"**.
- A trip that earns several labels is shown once with all of them.
- Every labelled offer can be opened and booked.
- Changing the travelcard updates prices and labels.
- A label is never wrong: fastest = shortest duration, cheapest = lowest total price, greenest = lowest total CO₂.
- A trip with a CO₂ value "not available" cannot be the greenest.

### 28 · One service for complete trip offers *(Partner app · Must)*
> As a partner app, I want one service that returns complete trip offers, so that I don't have to combine the partners' leg offers myself.

- Our **middleware** gets the leg offers from the Vertt API and from OJP / OJP Fare and combines them into whole trips.
- A trip is only built if every transfer has at least 8 minutes.
- It calculates total duration, total price and total CO₂ of every trip.
- The booking demo gets its trip offers only from the middleware.
- The middleware is not a public service (decided 2026-10-05): one entrance for our own frontend; the partner interfaces and the model are called from the server only.
- The answer is JSON and documented in `docs/api/trip-offers.md`.

### 29 · The model decides, the numbers stay right *(Demo presenter · Must)*
> As a demo presenter, I want an AI model to decide which trip is the fastest, the cheapest and the greenest, so that I can show a model working on real partner offers – without ever showing a wrong result.

- The middleware asks **Jev 1.13** (TypeSafe) through **OpenRouter** to choose, for each label, one of the trips it built.
- The model gets the calculated totals, and nothing about the customer.
- Every decision is **checked against the numbers**. If the model is wrong, unsure, slow or unreachable, the calculated result is shown.
- Each label says where it came from: model confirmed / model overruled / calculated. This is stored in the data link.
- The same trips always give the same labels during a demo, also when listed in a different order.
- Background: the model's makers state that it is not reliable at comparing numbers and times – hence the check. See the open question in PRD-8 about a "Recommended" label as a better task for the model.

## What the new stories change in stories 1–21

| Story | Change |
|---|---|
| 2 · Start and destination | **The customer types an address** (suggestions from the official Swiss address search, swisstopo); it is turned into coordinates, which go to the Vertt API. The API uses the nearest place it serves. The demo rule "nothing has to be typed" gets this one exception; pre-filled places keep the demo clickable. Findings: `docs/api/geocoding.md`. |
| 2 · Start and destination | The known places are no longer a list in the demo: they are the places the Vertt API serves plus official stations. The provided rides cover **Wettswil am Albis** and the stations **Zürich HB, Zürich Enge, Schlieren, Zürich Flughafen**. |
| 6 · List of connections | "Vertt only" is shown only if the Vertt API has an offer for the whole route – with the provided rides it has none for long routes. A Vertt → SBB → Vertt journey needs a Vertt offer at the destination, which the provided rides do not contain. |
| 6 · List of connections | The single bookable connection becomes up to three trip offers labelled fastest / cheapest / greenest (story 27). The two comparison cards stay. |
| 7 · Leg details | The car comes with the Vertt ride offer instead of a separate pool: each trip offer is built from one recorded ride and brings its car. Nothing is drawn at random. Line and platform come from OJP. |
| 11 · Why recommended | The "Recommended" tag is replaced by the three labels; "Door to door with one booking" stays. |
| 8 · Price | Vertt price from the Vertt API, train price from OJP Fare. |
| 9 · CO₂ | The car's CO₂ factor comes with the Vertt offer; it is missing for 3 of 9 cars → "not available" will really occur. OJP delivers a train value that is not 0 – conflicts with "tailpipe only" (CTO topic B7). |
| 10 · Map | Train geometry from OJP, street geometry from the Vertt API, cut near the home (story 26). |
| 17 · Booking data | The data link also stores the SBB price details (product, net price, VAT rate), the Vertt offer ID with "recorded / constructed", and the labels of the booked trip with where each came from. |

**To decide (with Tim / CTO):** the route service that gives distance and ride time for calculated Vertt offers (decided: Valhalla – see `docs/api/routing.md`); saver price as "the" SBB price; train CO₂ on screen; whether the whole demo gets an access code; what the model should really decide (labels as a checked second opinion, or an own "Recommended" label); whether trip values may be sent to OpenRouter (outside Switzerland, no personal data).

