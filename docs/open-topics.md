# Open topics – Prototype 1

Only what is **still open**. Everything decided is in [PRD.md](PRD.md) and the specs (`specs/PROJ-1-intermodal-booking-demo/2_PRDs/`). When a topic is decided, write the decision there and delete it here.

Last update: 2026-10-05.

## For the CTO

| # | Topic | Current default in Prototype 1 | Question |
|---|---|---|---|
| 1 | **Commission asymmetry** | Vertt earns 5 % on the train ticket, SBB earns nothing (deliberate demo decision) | OK to present like this to the partners? |
| 2 | **AI as showcase** | No AI in Prototype 1 (Jev dropped 2026-10-06) | Is an AI part wanted later, e.g. a "Recommended" label weighing time, price, CO₂ and transfers? |
| 3 | **Vertt's own route / price component** | Valhalla × Vertt tariff | Should Vertt's real component (or Google) replace Valhalla later, for prices closer to reality? |
| 4 | **Settlement timing** | Per booking | Real world: per booking or monthly batch? |
| 5 | **Unpaid invoice** | Invoice counts as paid immediately | What happens to the B2B share if the customer never pays? |
| 6 | **Payment fees** (card / TWINT, ~1–2 %) | Ignored | Who carries them – seller only or shared? |
| 7 | **Real cancellation rules** | Full refund, no fee | SBB refund rules; Vertt fee once the driver is on the way? |
| 8 | **Demo date / audience** | Not decided | When and to whom do we show it first? |

## For Vertt finance

| # | Topic | Default | Question |
|---|---|---|---|
| 9 | **VAT in the Vertt tariff** | Prices incl. 8.1 % VAT assumed | Do the tariff values include VAT, and at which rate? |

## With the Innovation Booster partners

| # | Topic | Default | Question |
|---|---|---|---|
| 10 | **Settlement data format** | Draft in PRD section 7 | Align with the partners' transaction layer before building? |

## To find out by trying (spikes)

| # | Topic | Where |
|---|---|---|
| 12 | Does OJP Fare offer a normal half-fare ticket (Streckenbillett), or only saver tickets? | PRD-6 |
| 13 | How close do Valhalla + tariff come to the 9 recorded rides? | PRD-7 |
| 14 | Which example address pair to pre-fill in the address fields? | PRD-1, PRD-8 |
| 15 | Which online store on Vercel holds the data behind the links? | PRD-5 |
