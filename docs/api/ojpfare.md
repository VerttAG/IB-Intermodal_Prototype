# OJP Fare – Data model (ticket prices)

Status: derived from **real responses** on 2026-10-05 (spike). Field names below appear exactly like this in the responses.
Related: [ojp20.md](ojp20.md) (journey planner, provides the input trip) · [PRD](../PRD.md) · [CTO meeting](../cto-meeting.md)

## 1. Overview

| | |
|---|---|
| Endpoint | `POST https://api.opentransportdata.swiss/ojpfare` |
| Auth | Header `Authorization: Bearer <OJP_FARE_API_KEY>` (from `.env`, separate key from OJP 2.0) |
| Content type | `application/xml` |
| Limits | 20,000 calls/day, 50 calls/minute |
| Status | **Beta** – prices come from **NOVA** (SBB price system) |
| Source of request format | Official implementation [openTdataCH/ojp-nova](https://github.com/openTdataCH/ojp-nova), example `xslt/test_ojpfare_request_2.0.xml` (cookbook pages returned 404 on 2026-10-05) |
| Product page | [api-manager … tedp_ojpfare-1](https://api-manager.opentransportdata.swiss/portal/catalogue-products/tedp_ojpfare-1) |

## 2. How it works – two steps

```
1. OJP 2.0  OJPTripRequest   ──►  TripResult/Trip   (see ojp20.md)
                                        │ copy the whole <Trip> element
                                        ▼
2. OJP Fare OJPFareRequest   ──►  OJPFareDelivery: price(s) for that trip
```

OJP Fare does not search connections itself – it prices a trip that OJP 2.0 found. So every price costs **two** API calls.

## 3. Request

```xml
<OJP xmlns="http://www.vdv.de/ojp" xmlns:siri="http://www.siri.org.uk/siri" version="2.0">
  <OJPRequest>
    <siri:ServiceRequest>
      <siri:RequestTimestamp>2026-10-05T11:29:00Z</siri:RequestTimestamp>
      <siri:RequestorRef>IB-Intermodal-Prototype</siri:RequestorRef>
      <OJPFareRequest>
        <siri:RequestTimestamp>2026-10-05T11:29:00Z</siri:RequestTimestamp>
        <TripFareRequest>
          <Trip> … copied 1:1 from the OJP 2.0 TripResult … </Trip>
        </TripFareRequest>
        <Params>
          <FareAuthorityFilter>ch:1:NOVA</FareAuthorityFilter>
          <PassengerCategory>Adult</PassengerCategory>
          <FareClass>secondClass</FareClass>
          <Traveller>
            <PassengerCategory>Adult</PassengerCategory>
            <EntitlementProducts>              <!-- travelcard, see table below -->
              <EntitlementProduct>
                <FareAuthorityRef>NOVA</FareAuthorityRef>
                <EntitlementProductRef>HTA</EntitlementProductRef>
                <EntitlementProductName>Halbtax</EntitlementProductName>
              </EntitlementProduct>
            </EntitlementProducts>
          </Traveller>
        </Params>
      </OJPFareRequest>
    </siri:ServiceRequest>
  </OJPRequest>
</OJP>
```

Map geometry (`LegTrack`, `LegProjection`) can be removed from the copied `Trip` – it is not needed for the price and makes the request much smaller.

### Travelcard (`Traveller/EntitlementProducts`)

| Travelcard (story 4) | What to send | Result in test |
|---|---|---|
| None | `<EntitlementProducts/>` (**empty element**) | ✅ works |
| None | `Traveller` without `EntitlementProducts`, or no `Traveller` at all, or with `Age` | ❌ HTTP 500 "Internal Server Error" |
| Half-fare | `EntitlementProductRef` = `HTA`, name `Halbtax` | ✅ works, `RequiredCard = HTA` |
| GA | `EntitlementProductRef` = `GA` (guessed) | ⚠️ HTTP 200, but same prices as "none" – GA **not recognised**. Correct code unknown |

### Params

| Element | Value used | Note |
|---|---|---|
| `FareAuthorityFilter` | `ch:1:NOVA` | Required |
| `PassengerCategory` | `Adult` | Prototype 1: 1 adult |
| `FareClass` | `secondClass` | ⚠️ Ignored – response contains both classes |

## 4. Response structure

```
OJP
└─ OJPResponse
   └─ siri:ServiceDelivery
      ├─ siri:ResponseTimestamp   2026-10-05T11:29:52.000949   (no timezone!)
      ├─ siri:ProducerRef         OJP2NOVA
      └─ OJPFareDelivery
         ├─ siri:ResponseTimestamp
         ├─ siri:Status           true
         └─ FareResult
            ├─ Id                 ID-EF0F…  (= Trip/Id of the request)
            └─ TripFareResult  (1..n, one per product offered)
               ├─ FromLegIdRef    1      ┐ which legs this price covers
               ├─ ToLegIdRef      1      ┘ (Leg/Id from the trip)
               └─ FareProduct
                  ├─ FareProductId        84004
                  ├─ FareProductName      Sparbillett | Streckenbillett
                  ├─ FareAuthorityRef     ch:1:sboid:101704
                  ├─ FareAuthorityText    Alliance SwissPass
                  ├─ Price                21.40     (CHF incl. VAT)
                  ├─ NetPrice             19.67     (CHF excl. VAT)
                  ├─ Currency             CHF
                  ├─ VatRate              8.1
                  ├─ FareClass            firstClass | secondClass
                  └─ RequiredCard         HTA       (only if a travelcard is needed)
```

### Fields we use

| Path (inside `TripFareResult`) | Example | Meaning | Use in project (story) |
|---|---|---|---|
| `FromLegIdRef`, `ToLegIdRef` | `1`, `1` | Legs covered by this price | Assign price to the train leg (8) |
| `FareProduct/Price` | `21.40` | Price incl. VAT | Train leg price (8), settlement (19, 20) |
| `FareProduct/NetPrice` | `19.67` | Price excl. VAT | Data link (17) |
| `FareProduct/VatRate` | `8.1` | VAT in % | Data link (17) – confirms 8.1 % |
| `FareProduct/Currency` | `CHF` | Currency | Check |
| `FareProduct/FareClass` | `secondClass` | Class | **Filter: 2nd class only** (PRD) |
| `FareProduct/FareProductName` | `Sparbillett` | Ticket type | Store in data link; saver vs. normal |
| `FareProduct/FareProductId` | `84004` | NOVA product ID | Data link |
| `FareProduct/RequiredCard` | `HTA` | Travelcard needed | Check that the half-fare price was applied (4) |

## 5. Test results – IC 8 Zürich HB 12:02 → Bern 12:58, Tue 2026-10-06

| Travelcard | Product | Class | Price | Net | Card |
|---|---|---|---|---|---|
| None | Sparbillett | 2nd | **CHF 38.80** | – | – |
| None | Streckenbillett | 1st | CHF 91.00 | – | – |
| Half-fare | Sparbillett | 2nd | **CHF 21.40** | 19.67 | HTA |
| Half-fare | Sparbillett | 1st | CHF 35.60 | 32.72 | HTA |
| GA | *(same as "none")* | | | | |

## 6. Quirks and findings

| # | Finding | Consequence |
|---|---|---|
| 1 | Several products per trip, both classes, regardless of `FareClass` | Our logic must pick: 2nd class, then cheapest (or a fixed product type) |
| 2 | Without travelcard, 2nd class only came as **Sparbillett** (saver, train-bound); the normal ticket only for 1st class | Unclear if a normal 2nd-class price is available – to clarify (CTO topic B8) |
| 3 | "No travelcard" needs an **empty** `<EntitlementProducts/>`; otherwise HTTP 500 without error message | Always send the element |
| 4 | GA code unknown (`GA` not recognised) | Prototype 1 uses its own rule: GA → CHF 0 |
| 5 | Response namespaces differ from the request: OJP as prefix `ns2:`, a default namespace `https://www.siri.org.uk/siri` (with https) | Parse by namespace URI `http://www.vdv.de/ojp`, not by prefix |
| 6 | `FareClass` value may contain a trailing space (`secondClass `) | Trim values |
| 7 | Response timestamp has no timezone | Don't use for logic |
| 8 | Beta service, saver prices change with demand and time of booking | Cache the result per booking; mark as "OJP Fare (beta)" |

## 7. Local test files (not in Git)

In `data/cache/` (gitignored): `fare_zurich_bern_half.xml`, `fare_zurich_bern_c_empty_entitlements.xml` (no travelcard), `fare_zurich_bern_d_ga.xml`.
