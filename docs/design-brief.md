# Design brief – Intermodal booking demo (Vertt × SBB)

Product brief for UX/UI design. Owner: Tim Diethelm. Date: 2026-10-06.
Reference mockup (flow only, not the look): https://ib-intermodal-prototype.vercel.app – password from Tim – or `mockup/index.html` in this repo.

## 1. What it is

A clickable booking demo for the Innovation Booster project with SBB. A customer enters any two Swiss addresses and gets **door-to-door trips that combine Vertt and the train**: a Vertt ride to a main station, the train, and a Vertt ride (or a short walk) to the destination – booked and paid **once**, in one app.

The demo runs in two modes, chosen at the start: **"Vertt app"** or **"SBB app"**. Both look the same; only the app name and who the customer pays change. Behind the scenes every booking creates settlement data for the project partners – the customer never sees it, but a small link on the receipt opens it.

**Audience of the demo:** the Vertt CTO and the Innovation Booster partners, shown by a presenter on a laptop or phone. It must feel like a real, calm, trustworthy booking app.

## 2. Design goal

- The **trip choice (step 1) is the heart** of the demo: it must be immediately clear which part is Vertt, which is train, which is walking – and why one trip is fastest, another cheapest, another greenest.
- **Price and CO₂ per leg** must be easy to compare.
- Everything else (login, payment, receipt) should be quick and unobtrusive.

## 3. Screens and flow

| # | Screen | What the customer sees and does |
|---|---|---|
| 0 | **Choose app** | Two options: "Vertt app" / "SBB app" (each "sells the whole journey"). Fixed until the booking is paid or the page is reloaded. |
| 1 | **Plan** | **From** and **To**: address fields with suggestions while typing (empty at start). **Depart at**: date and time. **Travelcard**: no travelcard / half-fare / GA (half-fare preselected), or **"Log in with SwissPass"**. **Search** button (enabled once both addresses are chosen). |
| 1a | **SwissPass mock login** | Opens from "Log in with SwissPass": a SwissPass-style login with pre-filled fields (nothing to type), the customer picks a **test profile** (no travelcard / half-fare / GA) and logs in with one click. Afterwards the travelcard is set and locked ("from SwissPass"), and **step 2 (login) is skipped** later. |
| 1b | **Searching** | Loading state, up to about 5 seconds. |
| 1c | **Results** | Up to **3 bookable trips**, each with one or more labels **Fastest / Cheapest / Greenest** and the line "Door to door with one booking". Per card: departure – arrival, total duration, number of transfers, a bar showing the legs (Vertt / train / walk), **the car of each Vertt ride with its CO₂** (e.g. "Renault Talisman · 120 g/km"), total price, total CO₂. Below: two **comparison cards** "Vertt only" and "Public transport only" – greyed, not clickable, not bookable. |
| 1d | **Trip details** | Map of the whole trip (Vertt, train and walking in different line styles, with a legend). Leg by leg: **Vertt ride** (car arrives 5 min after the departure time, or 2 min after the train; car make, model, year, g/km; km, minutes, price, CO₂) · **transfer** time · **train** (line, platform, times, price with "half-fare price" or "covered by GA", CO₂) · **walk** (minutes, distance). Total price and CO₂. Buttons: Continue / Back to connections. |
| 2 | **Log in** | One click each: Google, Apple, SwissPass (opens the SwissPass mock login without profile choice), or email + password (pre-filled, not editable). Skipped if SwissPass was used in step 1. |
| 3 | **Overview & pay** | Map and legs again, total, CO₂, travelcard. Clear statement **"You pay [Vertt / SBB] for the whole journey"**. **Promo**: tick 5 %, 10 % or 20 % off the Vertt rides (one at most, can be unticked; the Vertt price shows old and new price). **Payment method**: card, TWINT, invoice, business – none preselected. "Pay CHF …" (enabled once a method is chosen). No back button. |
| 3a | **Paying** | Short payment animation ("Paying Vertt …"). |
| 4 | **Receipt** | "Paid" with booking number, seller, route, amount per leg, discount, total, travelcard, payment method. Buttons **Cancel journey** (with a "Really cancel?" confirmation → receipt shows "Cancelled" and the refund) and **New booking**. A small link "Settlement data (for project partners)" that opens the booking data with a copy button. **Export** of all bookings made in this browser, and "Clear list". |

## 4. States and messages to design

- Address not found / outside Switzerland
- Start and destination less than 10 km apart: **"Trip not suitable for intermodal journey"**
- No trip found for this time (e.g. at night)
- Too many searches: "Too many searches, please wait a moment"
- A value that is not available (e.g. CO₂): shown as "not available", never 0
- Cancelled booking (receipt)
- Loading (search, payment)

## 5. Content rules

- Always **1 adult, 2nd class**.
- Prices in **CHF** with two decimals, rounded to 0.05 (e.g. CHF 33.05). Each leg has its own price; the total is the sum.
- **CO₂** in **kg** with one decimal per leg and in total; cars additionally in **g/km**.
- Travelcard affects only the train price: half-fare price, ×2 without travelcard, CHF 0.00 with GA ("covered by GA").
- The labels are calculated: Fastest = earliest arrival, Cheapest = lowest price, Greenest = lowest CO₂. One trip can carry several labels.
- Times are Swiss local time.

## 6. Design guidance

- **Phone layout**; on a laptop the phone screen sits in the middle.
- **One neutral design for both modes.** No official SBB or Vertt logos, fonts or brand colours (the demo is shown publicly to partners). A neutral accent colour; the Vertt app's patterns can be reused where they fit.
- Functional and calm: light background, white cards, thin dividers, small corner radius, clear hierarchy (times and prices bold, details smaller) – no decorative elements, no emojis.
- Vertt, train and walk must be distinguishable **not only by colour** (label or pattern as well).
- Accessible contrast and touch targets; everything also works with the keyboard.

## 7. Fixed vs. free

| Fixed | Free |
|---|---|
| Order of the steps and what each screen contains (section 3) | Layout, visual design, components, icons |
| Content rules (section 5), the messages' meaning (section 4) | Exact wording and microcopy |
| SwissPass mock login skips step 2 | How the map, the leg bar and the labels look |
| Comparison cards are not bookable | Animation of loading and payment |

## 8. Open / later

- A pre-filled example address pair may be added later (fields start empty for now).
- Smaller stations and more cars come later; the design should not depend on a fixed number of cars or stations.
- Deliverables and timing: to agree with Tim (e.g. screens 0–4 plus the states in section 4).
