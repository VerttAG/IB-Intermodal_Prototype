# Data schema – booking data link and export

The data that every booking of the demo produces for the Innovation Booster partners. Produced by `src/settlement.py`, rules in [PRD.md](PRD.md) section 6, requirements in PRD-5 (`specs/PROJ-1-intermodal-booking-demo/2_PRDs/`).

Last update: 2026-10-19. A change to a field name or meaning is always a visible change to this file.

## 1. Where the data comes from

| Output | What you get |
|---|---|
| **Data link** (receipt → "Settlement data (for project partners)") | `GET /api/bookings?id=BK-123456` – one **booking record** as JSON. Behind the demo password. After a cancellation the same link shows the updated record. |
| **Export** (receipt → "Export") | File `bookings.json` – a JSON **list of booking records**, all bookings made in this browser since the last "Clear", in their current state (incl. cancelled ones). |
| Unknown booking ID | `404` with `{"version": "1", "status": "not_found"}` |

Only transactional data: no names, addresses, coordinates, stations, times of the legs or cars.

## 2. Booking record

```
{ "booking": {...}, "legs": [...], "co2_total_kg": 1.288, "settlement_events": [...] }
```

| Field | Type | Meaning |
|---|---|---|
| `booking` | object | The booking (section 3) |
| `legs` | list | Amount and CO₂ per paid leg (section 4) |
| `co2_total_kg` | number | CO₂ of the whole trip in kg, 3 decimals = sum of the legs |
| `settlement_events` | list | All money movements, in order (section 5) |

## 3. `booking`

| Field | Type | Allowed values / format | Meaning |
|---|---|---|---|
| `booking_id` | string | `BK-` + 6 digits, e.g. `BK-240891` | Booking number, also on the receipt |
| `system` | string | `vertt` · `sbb` | App that sold the journey = **seller**, the party the customer pays |
| `status` | string | `paid` · `cancelled` | Current state. A booking exists from the click on "Pay" |
| `customer` | string | `demo-` + 4 hex characters | Pseudonymous demo customer ID, new for every booking. Not a real person |
| `login_method` | string | `google` · `apple` · `swisspass` · `email` | How the customer logged in (mock) |
| `travelcard` | string | `none` · `half` · `ga` | Travelcard; affects only the train price |
| `promo_percent` | integer | `0` · `5` · `10` · `20` | Promo on the Vertt rides |
| `promo_chf` | number | CHF ≥ 0 | Discount in CHF, carried by Vertt |
| `payment_method` | string | `card` · `twint` · `invoice` · `business` | Payment method (mock; all count as paid immediately) |
| `booked_at` | string | ISO 8601 with time zone, Swiss time | Click on "Pay" |
| `total_chf` | number | CHF, multiple of 0.05 | What the customer paid = sum of `legs[].amount_chf` |

## 4. `legs[]`

One entry per **Vertt ride** and **one** entry for the SBB ticket (all train legs of the trip together). Walks are not listed (no amount, no CO₂).

| Field | Type | Allowed values / format | Meaning |
|---|---|---|---|
| `seq` | integer | 1, 2, 3 … | Order in the trip |
| `operator` | string | `Vertt` · `SBB` | Who provides the leg |
| `type` | string | `vertt_ride` · `train` | Kind of leg |
| `amount_chf` | number | CHF, multiple of 0.05 | Price the customer pays for this leg – after promo (Vertt) or travelcard (SBB; `0` with GA) |
| `co2_kg` | number | kg, 3 decimals | CO₂ of this leg (Vertt: km × car's g/km; train: from SBB's OJP) |

## 5. `settlement_events[]`

**Append-only:** events are never changed or deleted. A cancellation adds new events at the end.

| Field | Type | Allowed values / format | Meaning |
|---|---|---|---|
| `event_id` | string | `<booking_id>-ev<seq>`, e.g. `BK-240891-ev2` | Unique ID of the event |
| `booking_id` | string | as in `booking` | Booking the event belongs to |
| `seq` | integer | 1, 2, 3 … | Order within the booking |
| `timestamp` | string | ISO 8601 with time zone, Swiss time | When it happened (payment = `booked_at`) |
| `event_type` | string | see below | Kind of money movement |
| `payer` | string | `customer` · `Vertt` · `SBB` | Who pays |
| `payee` | string | `customer` · `Vertt` · `SBB` | Who receives |
| `amount_chf` | number | CHF > 0, two decimals | Amount |
| `reason` | string | free text in English | Short explanation for people, not for machines |
| `refers_to_event` | string or `null` | an `event_id` of the same booking | For `refund` and `reversal`: the event that is undone. Otherwise `null` |

| `event_type` | When | Payer → payee |
|---|---|---|
| `b2c_payment` | Booking | customer → seller, `total_chf` |
| `b2b_transfer` | Booking | **Vertt app:** Vertt → SBB, train ticket · **SBB app:** SBB → Vertt, all Vertt rides |
| `commission` | Booking, Vertt app only | SBB → Vertt, 5 % of the train ticket |
| `refund` | Cancellation | seller → customer, the full payment |
| `reversal` | Cancellation | one per `b2b_transfer` and `commission`, payer and payee swapped, same amount |

Events with amount 0 are not written: with GA the Vertt app has no transfer and no commission.

## 6. Rules for the numbers

- All amounts in **CHF including VAT** (8.1 %), as JSON numbers with at most two decimals (`38.4` = CHF 38.40).
- Customer amounts (`legs`, `total_chf`, `b2c_payment`, `refund`) are rounded to CHF 0.05; B2B amounts are exact to the centime, the commission rounded half up.
- Settled **per booking**. Vertt and SBB are one party each.
- Summing all events per party gives what each party ends with; after a cancellation everyone is back at 0.

## 7. Examples

**Vertt app, half-fare, cancelled** (Vertt ride CHF 30.00, train CHF 8.40):

```json
{
 "booking": {"booking_id": "BK-240891", "system": "vertt", "status": "cancelled", "customer": "demo-3f9a",
  "login_method": "swisspass", "travelcard": "half", "promo_percent": 0, "promo_chf": 0.0,
  "payment_method": "twint", "booked_at": "2026-10-19T08:12:05+02:00", "total_chf": 38.4},
 "legs": [
  {"seq": 1, "operator": "Vertt", "type": "vertt_ride", "amount_chf": 30.0, "co2_kg": 1.2},
  {"seq": 2, "operator": "SBB", "type": "train", "amount_chf": 8.4, "co2_kg": 0.088}
 ],
 "co2_total_kg": 1.288,
 "settlement_events": [
  {"event_id": "BK-240891-ev1", "booking_id": "BK-240891", "seq": 1, "timestamp": "2026-10-19T08:12:05+02:00",
   "event_type": "b2c_payment", "payer": "customer", "payee": "Vertt", "amount_chf": 38.4,
   "reason": "Customer pays the seller for the whole journey", "refers_to_event": null},
  {"event_id": "BK-240891-ev2", "booking_id": "BK-240891", "seq": 2, "timestamp": "2026-10-19T08:12:05+02:00",
   "event_type": "b2b_transfer", "payer": "Vertt", "payee": "SBB", "amount_chf": 8.4,
   "reason": "Train ticket sold by Vertt", "refers_to_event": null},
  {"event_id": "BK-240891-ev3", "booking_id": "BK-240891", "seq": 3, "timestamp": "2026-10-19T08:12:05+02:00",
   "event_type": "commission", "payer": "SBB", "payee": "Vertt", "amount_chf": 0.42,
   "reason": "5 % sales commission on the train ticket", "refers_to_event": null},
  {"event_id": "BK-240891-ev4", "booking_id": "BK-240891", "seq": 4, "timestamp": "2026-10-19T08:20:41+02:00",
   "event_type": "refund", "payer": "Vertt", "payee": "customer", "amount_chf": 38.4,
   "reason": "Journey cancelled, full refund", "refers_to_event": "BK-240891-ev1"},
  {"event_id": "BK-240891-ev5", "booking_id": "BK-240891", "seq": 5, "timestamp": "2026-10-19T08:20:41+02:00",
   "event_type": "reversal", "payer": "SBB", "payee": "Vertt", "amount_chf": 8.4,
   "reason": "Reversal of b2b_transfer", "refers_to_event": "BK-240891-ev2"},
  {"event_id": "BK-240891-ev6", "booking_id": "BK-240891", "seq": 6, "timestamp": "2026-10-19T08:20:41+02:00",
   "event_type": "reversal", "payer": "Vertt", "payee": "SBB", "amount_chf": 0.42,
   "reason": "Reversal of commission", "refers_to_event": "BK-240891-ev3"}
 ]
}
```

**SBB app, GA, 10 % promo** – only the events (Vertt ride CHF 30.00 → 27.00, train CHF 0.00):

```json
[
 {"event_id": "BK-990298-ev1", "seq": 1, "event_type": "b2c_payment", "payer": "customer", "payee": "SBB", "amount_chf": 27.0, "refers_to_event": null},
 {"event_id": "BK-990298-ev2", "seq": 2, "event_type": "b2b_transfer", "payer": "SBB", "payee": "Vertt", "amount_chf": 27.0, "refers_to_event": null}
]
```
