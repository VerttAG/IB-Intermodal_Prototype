# PROJ-1-PRD-4: Settlement between operators and cancellation

## Status: Planned

Covers the money movements each booking produces and what a cancellation adds. No screen shows the settlement; it exists as data (PROJ-1-PRD-5). Source: [docs/PRD.md](../../../docs/PRD.md) section 6, [docs/user-stories.md](../../../docs/user-stories.md) stories 18, 19, 20. Story numbers are given in brackets.

Terms used below: **train part** = price of all SBB legs after travelcard. **Vertt part** = price of all Vertt legs after promo. **Total** = train part + Vertt part. The train part is the price stored in the booking (from OJP Fare, PROJ-1-PRD-6); the Vertt part is based on the Vertt ride offers (PROJ-1-PRD-7).

## User Stories

### US-1: As Vertt, when a customer books the whole journey in my app, I want to collect the full price and pass SBB's share on minus a 5 % commission so that I'm rewarded for selling SBB tickets and SBB still gets its money (story 19)
**Given** the Vertt app was chosen
**When** the customer pays
**Then** the customer pays the total to Vertt
**And** Vertt passes the train part to SBB, and SBB pays Vertt a 5 % commission as a separate entry

**Acceptance Criteria:**
- [ ] AC-1: Event "customer → Vertt" (`b2c_payment`) with the total.
- [ ] AC-2: Event "Vertt → SBB" (`b2b_transfer`) with the train part.
- [ ] AC-3: A separate event "SBB → Vertt" (`commission`) with 5 % of the train part. The commission is never netted into the transfer.
- [ ] AC-4: With half-fare, transfer and commission are based on the half-fare price.
- [ ] AC-5: With GA the train part is CHF 0: there is no transfer event and no commission event.
- [ ] AC-6: A promo lowers the customer payment and Vertt's own income only. Transfer and commission are the same with and without promo.

### US-2: As SBB, when a customer books the whole journey in my app, I want to collect the full price and pass Vertt's full share on so that Vertt is paid for its rides (story 20)
**Given** the SBB app was chosen
**When** the customer pays
**Then** the customer pays the total to SBB
**And** SBB passes the Vertt part to Vertt, with no commission

**Acceptance Criteria:**
- [ ] AC-7: Event "customer → SBB" (`b2c_payment`) with the total.
- [ ] AC-8: Event "SBB → Vertt" (`b2b_transfer`) with the Vertt part after promo.
- [ ] AC-9: There is no commission event in the SBB app.
- [ ] AC-10: Travelcards change only the train part. With GA, SBB passes the whole customer payment on and keeps CHF 0.00.

### US-3: As an operator, I want the money movements of every booking to follow fixed rules and add up so that the settlement data can be trusted (stories 19, 20, general rules)
**Given** any paid booking
**When** its settlement events are read
**Then** the amounts follow the rules above and add up to the customer payment

**Acceptance Criteria:**
- [ ] AC-11: B2B amounts (transfer, commission) are exact to the centime. Customer amounts are rounded to CHF 0.05.
- [ ] AC-11a: The settlement starts from the **rounded** leg amounts the customer paid (e.g. the Vertt part CHF 33.05, not the API's exact CHF 33.04), so that customer payment and B2B transfers add up.
- [ ] AC-12: Settlement is per booking: every event belongs to exactly one booking.
- [ ] AC-13: Vertt is one party. No event names a driver.
- [ ] AC-14: For a paid booking, what Vertt ends with plus what SBB ends with equals the customer payment.
- [ ] AC-15: The reference case holds (Vertt part CHF 30.00, train part CHF 8.40, no promo):

| Seller | Events | Vertt ends with | SBB ends with |
|---|---|---|---|
| Vertt app | customer → Vertt 38.40 · Vertt → SBB 8.40 · SBB → Vertt 0.42 | 30.42 | 7.98 |
| SBB app | customer → SBB 38.40 · SBB → Vertt 30.00 | 30.00 | 8.40 |

### US-4: As a customer, I want to cancel my booked journey so that I get my money back if my plans change (story 18)
**Given** I am on the receipt of a paid booking
**When** I click "Cancel journey" and confirm
**Then** the receipt is marked "Cancelled" and shows my refund
**And** the money movements between the operators are reversed

**Acceptance Criteria:**
- [ ] AC-16: "Cancel journey" asks for confirmation ("Really cancel?"). Declining changes nothing.
- [ ] AC-17: After confirming, the receipt is marked "Cancelled" and shows the refund amount, which equals the total paid.
- [ ] AC-18: Only the whole journey can be cancelled. There is no way to cancel a single leg.
- [ ] AC-19: A booking can be cancelled once. After that "Cancel journey" is no longer offered.
- [ ] AC-20: The refund is the full amount with no fee.
- [ ] AC-21: A cancellation only adds events: a refund from the seller to the customer, a reversal of each B2B transfer, and a reversal of each commission.
- [ ] AC-22: Each reversal has the same amount as the event it reverses, with payer and payee swapped, and refers to that event.
- [ ] AC-23: Events that existed before the cancellation are unchanged afterwards: same content, same order.
- [ ] AC-24: After a cancellation, customer, Vertt and SBB each end with CHF 0.00 for this booking.
- [ ] AC-25: The booking status changes from "paid" to "cancelled".

## Edge Cases
- Vertt app + GA: the only event is the customer payment. A cancellation adds only the refund.
- SBB app + GA: customer payment and transfer have the same amount. A cancellation adds a refund and one reversal.
- Vertt app + promo 20 %: transfer and commission are identical to the same booking without promo (AC-6).
- 5 % of the train part is not a whole centime: rounded **half up** to the centime (0.4225 → 0.42, 0.425 → 0.43).
- "Cancel journey" is clicked twice quickly: one set of cancellation events.
- The events of a cancellation have a later time and a higher sequence number than the events of the payment.
- "New booking" after a cancellation starts a new run; the cancelled booking stays in the export.

## Open Questions
- ~~Rounding of the commission~~ → **Decided (Tim 2026-10-05):** half up to the centime.
- ~~Cancel after leaving the receipt~~ → **Decided (Tim 2026-10-05):** not possible. Once the receipt is left ("New booking" or reload), the booking stays "paid" in the export.
- Should the refund event refer to the original customer payment (like reversals refer to their event)? The lite mockup leaves it empty. → align with partners (cto-meeting B9).
- Is the commission asymmetry OK to present to partners (cto-meeting B2)?
- Real cancellation rules (B6) and settlement timing per booking vs. monthly (B3) are out of scope but should be confirmed.

## Dependencies
- Requires: PROJ-1-PRD-3 (payment creates the booking; "Cancel journey" sits on the receipt), PROJ-1-PRD-2 (leg prices), PROJ-1-PRD-6 and PROJ-1-PRD-7 (where the prices come from).
- Feeds: PROJ-1-PRD-5 (events are published in the data link and the export).

## Technical Requirements
- The rules are fixed; a user cannot change the commission rate or who carries the promo.
- Money is calculated without floating-point drift: results match the reference case to the centime.
- The event list of a booking is append-only.
- Amounts are in CHF including VAT. VAT on B2B transfers is out of scope.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: "Cancel journey" and the "Cancelled" receipt state of the lite mockup, [mockup/index.html](../../../mockup/index.html), live at https://ib-intermodal-prototype.vercel.app. The mockup's event logic illustrates the rules but is made-up data, not the reference.
- New component candidates: none.
- Design tokens: none defined yet.
- Interaction contract: confirm before cancelling, receipt switches to "Cancelled" with refund amount, cancel button disappears.
- Implementation tolerance: wording of the confirmation may change; the settlement rules and the reference case may not.
