# PROJ-1-PRD-3: Login and checkout

## Status: Planned

Covers step 2 (log in), step 3 (overview and pay) and the receipt. Source: [docs/PRD.md](../../../docs/PRD.md) section 4, [docs/user-stories.md](../../../docs/user-stories.md) stories 1b, 12–16. Story numbers are given in brackets. Cancelling from the receipt is in PROJ-1-PRD-4; the data link on the receipt is in PROJ-1-PRD-5.

## User Stories

### US-1: As a customer, I want to book my whole door-to-door journey in the app I already use so that I don't switch between apps (story 1b)
**Given** I chose one of the labelled trips in either app
**When** I go through login, overview and payment
**Then** all legs are booked together with one payment

**Acceptance Criteria:**
- [ ] AC-1: In both apps, all Vertt and SBB legs of the journey are booked in one flow with exactly one payment.
- [ ] AC-2: One booking with one booking number covers all legs.

### US-2: As a customer, I want to log in with an account I already have so that I can book without creating a new one (story 12)
**Given** I continue from the connection details and did not use SwissPass in step 1
**When** I pick a login option
**Then** I am logged in with one click and see the overview

**Acceptance Criteria:**
- [ ] AC-3: Four options are offered: Google, Apple, SwissPass, email + password. Each logs in with one click.
- [ ] AC-4: The email and password fields are pre-filled with demo values and cannot be edited.
- [ ] AC-5: Step 2 is not shown if SwissPass was used in step 1.
- [ ] AC-6: Choosing SwissPass in step 2 does not change the travelcard chosen in step 1, and does not lock it afterwards.
- [ ] AC-7: The booking stores the `login_method` (google, apple, swisspass, email) and a pseudonymous demo customer ID.

### US-3: As a customer, I want to see everything I'm about to book on one screen before I pay so that I can check it (story 13)
**Given** I am logged in
**When** the overview opens
**Then** I see the whole journey with prices, CO₂ and travelcard
**And** I see whom I pay

**Acceptance Criteria:**
- [ ] AC-8: The overview shows the map, start → destination, date and time, all legs with carrier and times, price per leg and total, CO₂ per leg and total, and the travelcard.
- [ ] AC-9: It states "You pay Vertt for the whole journey." in the Vertt app and "You pay SBB for the whole journey." in the SBB app.
- [ ] AC-10: There is no back button on the overview.

### US-4: As a customer, I want to apply a promo code before paying so that I get the discount I was promised (story 14)
**Given** I am on the overview
**When** I tick 5 %, 10 % or 20 %
**Then** the Vertt part gets cheaper and the total updates
**And** the train price stays the same

**Acceptance Criteria:**
- [ ] AC-11: A "promo code" area offers 5 %, 10 % and 20 %. At most one can be ticked, and the tick can be removed.
- [ ] AC-12: The discount applies to every Vertt leg and to no SBB leg.
- [ ] AC-13: Each discounted Vertt leg shows old and new price (e.g. "CHF 23.90 → CHF 21.50"), the new price rounded to CHF 0.05.
- [ ] AC-14: The total and the amount on the pay button update at once.
- [ ] AC-15: Removing the tick restores the original prices.
- [ ] AC-16: The behaviour is the same in both apps.
- [ ] AC-17: The booking stores the percentage, the discount in CHF, and that Vertt carries the discount.

### US-5: As a customer, I want to pay the way I'm used to so that booking fits my habits (story 15)
**Given** I am on the overview
**When** I choose a payment method
**Then** I can pay

**Acceptance Criteria:**
- [ ] AC-18: Four methods are offered: card, TWINT, invoice, business. None is selected when the overview opens.
- [ ] AC-19: "Pay" is disabled until a method is chosen, and shows the amount to pay.
- [ ] AC-20: No payment data is asked for (no card number, no phone number, no address).
- [ ] AC-21: Every method counts as paid immediately, with no payment fee added.
- [ ] AC-22: The booking stores the `payment_method`.

### US-6: As a customer, I want to pay with one click and immediately see a receipt so that I know my booking is confirmed (story 16)
**Given** a payment method is chosen
**When** I click "Pay"
**Then** I see a short payment animation and then the receipt

**Acceptance Criteria:**
- [ ] AC-23: After "Pay" a short payment animation naming the seller is shown, then the receipt.
- [ ] AC-24: The receipt is shown for every payment method.
- [ ] AC-25: The receipt shows booking number, seller, date, start → destination, each leg with carrier and price, the discount, the total, the travelcard and the payment method.
- [ ] AC-26: The receipt has the buttons "Cancel journey" (PROJ-1-PRD-4) and "New booking", and the data link (PROJ-1-PRD-5).
- [ ] AC-27: "New booking" starts a new run at step 0 with a newly drawn car. Earlier bookings stay in the export.

## Edge Cases
- "Pay" is clicked twice quickly: exactly one booking is created.
- The page is reloaded during the payment animation: the booking exists from the moment "Pay" is clicked – it is in the export with its settlement events, but its receipt is not shown and it cannot be cancelled any more (PROJ-1-PRD-4).
- Promo with two Vertt legs: each leg is discounted and rounded on its own; the stored discount in CHF is the difference between the totals before and after.
- Promo with GA: the customer pays the discounted Vertt part only.
- A promo is ticked, then the customer pays without removing it: the discounted prices are the booked prices and appear on the receipt.
- Login via SwissPass in step 2 with travelcard "none" chosen in step 1: the travelcard stays "none" (AC-6).
- No booking without a discount shows a discount line with CHF 0.00 on the receipt.
- The train price is a saver price that changes over time: the price shown in the overview is the price paid and stored (PROJ-1-PRD-6 AC-22, AC-23).
- A leg price is "not available": "Pay" stays disabled.

## Open Questions
- ~~Reload during the payment animation~~ → **Decided (Tim 2026-10-05):** the booking exists from the moment "Pay" is clicked.
- ~~`booked_at` vs. a fixed scenario departure~~ → no longer an issue: the customer chooses the departure time (PROJ-1-PRD-1), so `booked_at` is the real clock time of the click. A trip whose departure has already passed cannot be booked.
- Real-world topics that the demo ignores and the CTO should confirm: unpaid invoice (cto-meeting B4), payment fees (B5).

## Dependencies
- Requires: PROJ-1-PRD-1 (app, travelcard, SwissPass login), PROJ-1-PRD-2 (legs, prices, CO₂, map, car), and through it PROJ-1-PRD-6 (train prices) and PROJ-1-PRD-7 (Vertt prices).
- Feeds: PROJ-1-PRD-4 (the payment creates the first settlement events; "Cancel journey"), PROJ-1-PRD-5 (booking stored for data link and export).

## Technical Requirements
- No real login and no real payment: nothing is sent to Google, Apple, SwissPass, TWINT or a card provider.
- The demo email and password are obvious demo values and no real person's data.
- Login options, promo ticks, payment methods and "Pay" work with a pointer and with the keyboard; the disabled state of "Pay" is announced.
- The payment animation is short (about 1–2 seconds) and does not block the receipt if animations are reduced on the device.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: screens "login", "overview", "paying" and "receipt" of the lite mockup, [mockup/index.html](../../../mockup/index.html), live at https://ib-intermodal-prototype.vercel.app.
- New component candidates: discount line with CHF amount on the receipt (the mockup shows the percentage only).
- Design tokens: none defined yet.
- Interaction contract: one-click login, promo tick with live price update, payment method enabling "Pay", animation then receipt, no back button on the overview.
- Implementation tolerance: layout and wording may change; the receipt fields, the rounding and "no back button" may not.
