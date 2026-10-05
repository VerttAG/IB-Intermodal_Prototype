# PROJ-1-PRD-5: Booking data link and export

## Status: Planned – blocked by decision T1 (cto-meeting)

Covers the output for the Innovation Booster partners: one data link per booking, an export of all bookings, and the rule that none of it contains personal data. Source: [docs/PRD.md](../../../docs/PRD.md) section 7, [docs/user-stories.md](../../../docs/user-stories.md) stories 17, 21. Story numbers are given in brackets.

## User Stories

### US-1: As an IB partner, I want a link to the complete data of each booking so that I can feed real-looking bookings into our transaction layer (story 17)
**Given** a booking was paid
**When** I open its data link
**Then** I see the booking, the trip and all settlement events as JSON

**Acceptance Criteria:**
- [ ] AC-1: The receipt shows a link labelled "Settlement data (for project partners)" with a copy button.
- [ ] AC-2: The copy button puts the link on the clipboard and confirms it.
- [ ] AC-3: Opening the link shows valid JSON with three parts: booking, trip, settlement events.
- [ ] AC-4: The booking part contains `booking_id`, `system` (vertt / sbb), `login_method`, `travelcard`, `promo_percent`, `promo_chf`, `payment_method`, `booked_at`, `status` and a pseudonymous demo customer ID.
- [ ] AC-5: The trip part contains every leg with carrier, times, line or car category, price and CO₂, the car of each Vertt leg (make, model, year, CO₂ factor), and the data source of each value.
- [ ] AC-5a: Each train leg also carries what OJP Fare delivered with the price: product name, product ID, price without VAT and VAT rate (PROJ-1-PRD-6 AC-20).
- [ ] AC-5b: Each Vertt leg also carries the offer ID of the Vertt API and its assumptions: calculated, tariff region, factor, car drawn from the pool, waiting time (PROJ-1-PRD-7 AC-5).
- [ ] AC-5c: The trip part carries the labels of the booked trip (fastest, cheapest, greenest – all calculated) and the candidate stations of the search, each with its origin: "model" (with the model's name and version) or "code fallback" (PROJ-1-PRD-8 AC-15).
- [ ] AC-6: Each settlement event contains `event_id`, `booking_id`, `seq`, `timestamp`, `event_type` (b2c_payment, b2b_transfer, commission, refund, reversal), `payer`, `payee`, `amount_chf`, `reason`, `refers_to_event`.
- [ ] AC-7: The values in the link equal what the customer saw on the receipt (legs, prices, discount, total, travelcard, payment method).
- [ ] AC-8 *(pending T1)*: A partner can open the link on their own computer, not only in the browser where the booking was made.

### US-2: As an IB partner, I want the same link to show the booking after a cancellation so that I can follow one booking through its whole life (stories 17, 18)
**Given** I have the data link of a booking
**When** the booking is cancelled
**Then** the same link shows status "cancelled" and the added events

**Acceptance Criteria:**
- [ ] AC-9 *(pending T1)*: After a cancellation, the link that was copied before the cancellation shows the updated content.
- [ ] AC-10: The updated content has `status = cancelled` and the cancellation events appended after the original events (PROJ-1-PRD-4).

### US-3: As an IB partner, I want to export all bookings as one file so that I can load a whole demo session at once (story 17)
**Given** several bookings were made in this browser
**When** I export
**Then** I get one file with all of them, including cancelled ones

**Acceptance Criteria:**
- [ ] AC-11: The export contains every booking made since the page was first opened in this browser, in the same structure as the data link.
- [ ] AC-12: Bookings survive a page reload and "New booking".
- [ ] AC-13: Cancelled bookings are included with their current content.
- [ ] AC-14: "Clear" removes all stored bookings; the next export contains only bookings made after it.
- [ ] AC-15: The export is one valid JSON file.

### US-4: As an IB partner, I want the field names to be documented and stable so that my import does not break (story 17)
**Given** I build an import for the data
**When** I read the schema document
**Then** every field of the data link and the export is described

**Acceptance Criteria:**
- [ ] AC-16: `docs/schema.md` describes every field of the data link and the export, with type, meaning and allowed values.
- [ ] AC-17: Every data link and export produced by the demo matches `docs/schema.md`.
- [ ] AC-18: A change of a field name or meaning is a visible change to `docs/schema.md`, not a silent one.

### US-5: As Vertt, I want the demo, the code and the data to contain no personal customer data so that we comply with data protection and can share everything with the partners (story 21)
**Given** the repo is public and partners receive links and exports
**When** anyone looks at the repo, the page, a data link or an export
**Then** they find no personal data

**Acceptance Criteria:**
- [ ] AC-19: No names, emails, home addresses or real passenger IDs appear in the repo, on the page, in data links or in the export.
- [ ] AC-20: Known places are localities or stations only.
- [ ] AC-21: An address entered by the customer is not stored and not passed on.
- [ ] AC-22: The customer ID is a pseudonymous demo ID that cannot be traced to a real person.
- [ ] AC-23: The car pool contains make, model, year and CO₂ factor only – no number plates.

## Edge Cases
- Export with no bookings: an empty, valid result, or the export is not offered. No error.
- "Clear" is clicked by mistake: it asks for confirmation first, because the bookings cannot be brought back.
- The browser does not allow storing data (private window): the demo still works for the current run and says that the export will not survive a reload.
- Two tabs of the demo are open: bookings from both end up in the same export, none is lost.
- Two bookings get the same booking number: must not happen; booking numbers are unique within the stored bookings.
- A data link for an unknown or cleared booking is opened: a clear "booking not found" message, not an empty page.
- The clipboard is not available: the link can still be selected and copied by hand.
- A value has no real source (placeholder or estimate): its data source says so; it is never presented as measured.

## Open Questions
- **T1 – where does the data behind the link live?** This decides AC-8 and AC-9:
  - A (small online storage): both hold as written.
  - B (data inside the link, second link after cancellation): AC-8 holds, AC-9 changes to "a new link shows the cancelled booking".
  - C (export file only): AC-8 and AC-9 are dropped; the link works only in the presenter's browser.
  → CTO. The lite mockup shows the JSON in a pop-up and has no export yet.
- Does "Clear" also invalidate data links already sent to partners (only relevant for option A)? → Tim.
- Align the event format with the partners' transaction layer before building (cto-meeting B9)?
- Mark estimated values in the data link only, or also on screen (B1)?

## Dependencies
- Requires: PROJ-1-PRD-3 (booking), PROJ-1-PRD-4 (settlement events, cancellation), PROJ-1-PRD-2 (legs, car, data sources), PROJ-1-PRD-6 (SBB price details), PROJ-1-PRD-7 (Vertt offer ID, data basis), PROJ-1-PRD-8 (labels and their origin).
- Blocked by: cto-meeting T1 (storage of the data behind the link) and hosting (T3 row 11, GitHub issue #16).

## Technical Requirements
- The output is valid JSON with stable field names; amounts are numbers in CHF, timestamps carry a time zone.
- No personal data in any output (US-5). This also applies to logs and to anything stored online if T1 = A.
- API keys are never part of the page, a data link or an export.
- The copy button and the export work with a pointer and with the keyboard.

## UI Implementation Notes
- Project mode: new prototype, built in this repo (full chain).
- Reuse: data link note and JSON pop-up with copy button on the "receipt" screen of the lite mockup, [mockup/index.html](../../../mockup/index.html), live at https://ib-intermodal-prototype.vercel.app.
- New component candidates: "Export all bookings" and "Clear" controls; copy button next to the link itself. None are in the mockup.
- Design tokens: none defined yet.
- Interaction contract: copy link, open link, export, clear with confirmation.
- Implementation tolerance: where the export and clear controls sit is open; field names and structure follow `docs/schema.md`.
