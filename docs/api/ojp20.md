# OJP 2.0 – Data model (journey planner)

Status: derived from **real responses** on 2026-10-05 (spike). Field names below appear exactly like this in the responses.
Related: [ojpfare.md](ojpfare.md) (prices) · [PRD](../PRD.md) · [open topics](../open-topics.md)

## 1. Overview

| | |
|---|---|
| Endpoint | `POST https://api.opentransportdata.swiss/ojp20` |
| Auth | Header `Authorization: Bearer <OJP_API_KEY>` (from `.env`) |
| Content type | `application/xml` (request and response) |
| Limits | 20,000 calls/day, 50 calls/minute |
| Standard | VDV OJP 2.0 – [data model tables](https://vdvde.github.io/OJP/release/2.0/documentation-tables/ojp.html) |
| Namespaces | `http://www.vdv.de/ojp` (default) · `http://www.siri.org.uk/siri` (prefix `siri:`) |
| Covers | Current timetable period only |

Two request types are used in this project:

| Request | Question it answers | Used for (stories) |
|---|---|---|
| `OJPLocationInformationRequest` (LIR) | "Which stop is called *Zürich HB*?" → stop ID + coordinates | 2, 6 |
| `OJPTripRequest` (TR) | "Which connections go from A to B at time T?" → legs, times, platform, geometry, CO₂ | 6, 7, 9, 10 |

**What OJP 2.0 does not deliver:** prices (`IncludeFare` is accepted but ignored) → see [ojpfare.md](ojpfare.md).

## 2. Common envelope

Every request and response is wrapped the same way:

```
OJP  (version="2.0")
└─ OJPRequest / OJPResponse
   └─ siri:ServiceRequest / siri:ServiceDelivery
      ├─ siri:RequestTimestamp / siri:ResponseTimestamp
      ├─ siri:RequestorRef        (request: free name, we use "IB-Intermodal-Prototype")
      ├─ siri:ProducerRef         (response: server version, e.g. MENTZ-prod-…)
      └─ OJP<Type>Request / OJP<Type>Delivery   ← the actual content
```

## 3. LocationInformationRequest (find a stop)

### Request

```xml
<OJPLocationInformationRequest>
  <siri:RequestTimestamp>2026-10-05T11:22:00Z</siri:RequestTimestamp>
  <siri:MessageIdentifier>LIR-1</siri:MessageIdentifier>
  <InitialInput><Name>Zürich HB</Name></InitialInput>
  <Restrictions>
    <Type>stop</Type>                    <!-- only stops -->
    <NumberOfResults>3</NumberOfResults> <!-- guideline, server may return more -->
  </Restrictions>
</OJPLocationInformationRequest>
```

### Response structure

```
OJPLocationInformationDelivery
├─ siri:ResponseTimestamp, siri:RequestMessageRef, siri:DefaultLanguage, CalcTime (ms)
└─ PlaceResult  (1..n, best match first)
   ├─ Place
   │  ├─ StopPlace
   │  │  ├─ StopPlaceRef          ch:1:sloid:3000
   │  │  ├─ StopPlaceName/Text    Zürich HB
   │  │  ├─ PrivateCode           (System EFA, Value 108276) – internal, not used
   │  │  └─ TopographicPlaceRef   23026261:27 – municipality, not used
   │  ├─ Name/Text                Zürich HB (Zürich)
   │  ├─ GeoPosition
   │  │  ├─ siri:Longitude        8.54021
   │  │  └─ siri:Latitude         47.37818
   │  └─ Mode  (0..n)
   │     ├─ PtMode                rail | bus | tram | …
   │     └─ siri:RailSubmode      local | interregionalRail | international | highSpeedRail
   ├─ Complete                    true
   └─ Probability                 1  (0–1, how sure the match is)
```

### Fields we use

| Path | Example | Meaning | Use in project |
|---|---|---|---|
| `Place/StopPlace/StopPlaceRef` | `ch:1:sloid:3000` | Stop ID (SLOID). DIDOK 85**03000** → `sloid:3000` | Input for TripRequest |
| `Place/StopPlace/StopPlaceName/Text` | `Zürich HB` | Display name | Transfer point name |
| `Place/GeoPosition/siri:Latitude` / `Longitude` | `47.37818` / `8.54021` | WGS84 coordinates | Map marker; start/end of Vertt leg |
| `Place/Mode/PtMode` | `rail` | Which transport modes stop here | Pick the train station, not the bus stop |
| `Probability` | `1` | Match quality | Pick the best result |

**Quirk:** a search for "Zürich HB" also returns bus/tram stops ("Sihlpost/HB", "Bahnhofquai/HB"). Filter by `PtMode = rail`.

## 4. TripRequest (find connections)

### Request

```xml
<OJPTripRequest>
  <siri:RequestTimestamp>2026-10-05T11:23:00Z</siri:RequestTimestamp>
  <siri:MessageIdentifier>TR-1</siri:MessageIdentifier>
  <Origin>
    <PlaceRef>
      <StopPlaceRef>ch:1:sloid:3000</StopPlaceRef>
      <Name><Text>Zürich HB</Text></Name>
    </PlaceRef>
    <DepArrTime>2026-10-06T10:00:00Z</DepArrTime>   <!-- UTC! 10:00Z = 12:00 Swiss summer time -->
  </Origin>
  <Destination>
    <PlaceRef>
      <StopPlaceRef>ch:1:sloid:7000</StopPlaceRef>
      <Name><Text>Bern</Text></Name>
    </PlaceRef>
  </Destination>
  <Params>
    <NumberOfResults>2</NumberOfResults>
    <IncludeTrackSections>true</IncludeTrackSections>
    <IncludeLegProjection>true</IncludeLegProjection>   <!-- map geometry -->
    <IncludeFare>true</IncludeFare>                     <!-- accepted, but no prices returned -->
  </Params>
</OJPTripRequest>
```

Still to verify from the spec: how to search by **arrival** time (brief, trip 2) – not needed for Prototype 1 ("depart at" only).

### Response structure

```
OJPTripDelivery
├─ siri:ResponseTimestamp, siri:RequestMessageRef, siri:DefaultLanguage, CalcTime (ms)
├─ TripResponseContext
│  ├─ Places/Place (StopPlace | StopPoint | TopographicPlace, with Name + GeoPosition)
│  └─ Situations   (disruption messages, empty in test)
└─ TripResult  (1..n, one per connection)
   ├─ Id
   └─ Trip
      ├─ Id
      ├─ Duration          PT56M          (ISO 8601 duration)
      ├─ StartTime         2026-10-06T10:02:00Z   (UTC)
      ├─ EndTime           2026-10-06T10:58:00Z
      ├─ Transfers         0
      ├─ Distance          118217         (metres, whole trip)
      └─ Leg  (1..n)
         ├─ Id             1
         ├─ Duration       PT56M
         ├─ TimedLeg | TransferLeg | ContinuousLeg   ← exactly one, see below
         └─ EmissionCO2
            └─ KilogramPerPersonKm   0.007
```

### Leg type: `TimedLeg` (train, bus, tram – a scheduled service)

```
TimedLeg
├─ LegBoard  (where you get on)
│  ├─ siri:StopPointRef     ch:1:sloid:3000:500:31    (stop + platform-level ID)
│  ├─ StopPointName/Text    Zürich HB
│  ├─ NameSuffix/Text       PLATFORM_ACCESS_WITHOUT_ASSISTANCE   (accessibility)
│  ├─ PlannedQuay/Text      31          ← platform
│  ├─ ServiceDeparture/TimetabledTime   2026-10-06T10:02:00Z
│  ├─ Order                 1
│  └─ siri:ExpectedDepartureOccupancy  (0..2)
│     ├─ siri:FareClass       firstClass | secondClass
│     └─ siri:OccupancyLevel  manySeatsAvailable | …
├─ LegAlight  (where you get off) – same fields, ServiceArrival instead of ServiceDeparture
├─ Service
│  ├─ OperatingDayRef       2026-10-06
│  ├─ JourneyRef            ch:1:sjyid:100001:816-001
│  ├─ PublicCode            IC8
│  ├─ siri:LineRef          ojp:91008:E
│  ├─ siri:DirectionRef     R
│  ├─ Mode
│  │  ├─ PtMode             rail
│  │  ├─ siri:RailSubmode   highSpeedRail
│  │  ├─ Name/Text          Zug
│  │  └─ ShortName/Text     IC
│  ├─ ProductCategory (Name/Text InterCity, ShortName/Text IC, ProductCategoryRef 23)
│  ├─ PublishedServiceName/Text   IC8      ← line shown to customer
│  ├─ TrainNumber           816
│  ├─ Attribute (0..n)      (UserText/Text, Code, Importance) e.g. "Gratis-Internet …"
│  ├─ siri:OperatorRef      ojp:11
│  ├─ DestinationStopPointRef  ch:1:sloid:1609
│  └─ DestinationText/Text  Brig      ← final destination of the train
└─ LegTrack  (only with IncludeLegProjection=true)
   └─ TrackSection
      ├─ TrackSectionStart (StopPointRef, Name/Text)
      ├─ TrackSectionEnd   (StopPointRef, Name/Text)
      ├─ LinkProjection
      │  └─ Position (1..n)  – IC 8 Zürich–Bern: 1,761 points
      │     ├─ Longitude
      │     └─ Latitude
      ├─ Duration           PT56M
      └─ Length             118217   (metres, this leg)
```

### Leg type: `TransferLeg` (walking between platforms)

```
TransferLeg
├─ TransferType            walk
├─ LegStart (StopPointRef ch:1:sloid:2113:3:4, Name/Text Aarau)
├─ LegEnd   (StopPointRef ch:1:sloid:2113:3:5, Name/Text Aarau)
├─ Duration                PT4M
└─ PathGuidance/PathGuidanceSection/TrackSection
   └─ (same structure as LegTrack: start, end, LinkProjection/Position, Duration)
```
`EmissionCO2/KilogramPerPersonKm` = `0` for transfer legs.

`ContinuousLeg` (walking to/from an address, own transport) was not part of this test – expected when start/end are coordinates instead of stops (e.g. public-transport-only alternative, story 6).

### Fields we use

| Path (inside `Trip`) | Example | Meaning | Use in project (story) |
|---|---|---|---|
| `StartTime`, `EndTime` | `…T10:02:00Z` | Trip start/end, **UTC** | Connection card times (6) |
| `Duration` | `PT56M` | ISO 8601 duration | Card duration (6) |
| `Transfers` | `0` | Number of changes | Card (6) |
| `Distance` | `118217` | Metres, whole trip | – |
| `Leg/TimedLeg/LegBoard/StopPointName/Text` | `Zürich HB` | Boarding stop | Leg details (7) |
| `Leg/TimedLeg/LegBoard/PlannedQuay/Text` | `31` | Platform | Platform – Could (7) |
| `Leg/TimedLeg/LegBoard/ServiceDeparture/TimetabledTime` | `…T10:02:00Z` | Departure | Leg details, transfer check (7) |
| `Leg/TimedLeg/LegAlight/ServiceArrival/TimetabledTime` | `…T10:58:00Z` | Arrival | Leg details, transfer check (7) |
| `Leg/TimedLeg/Service/PublishedServiceName/Text` | `IC8` | Line | Leg details (7) |
| `Leg/TimedLeg/Service/Mode/PtMode` | `rail` | Mode | Mode icon (6, 7) |
| `Leg/TimedLeg/Service/DestinationText/Text` | `Brig` | Train's final destination | Optional display |
| `Leg/TimedLeg/LegTrack/TrackSection/LinkProjection/Position` | lat/lon list | Route geometry | Map (10) |
| `Leg/TimedLeg/LegTrack/TrackSection/Length` | `118217` | Leg distance in metres | CO₂ calculation (9) |
| `Leg/EmissionCO2/KilogramPerPersonKm` | `0.007` | CO₂ factor per person-km | CO₂ (9) – see note |
| `Leg/TransferLeg/Duration` | `PT4M` | Walking time between trains | Transfer row (7) |
| *(whole `Trip` element)* | – | – | **Input for OJP Fare** ([ojpfare.md](ojpfare.md)) |

### CO₂ per leg

`CO₂ [kg] = TrackSection/Length [m] / 1000 × EmissionCO2/KilogramPerPersonKm`
→ IC 8 Zürich–Bern: 118.217 km × 0.007 = **0.83 kg**.

The method behind 0.007 kg/pkm is not stated in the response (probably includes electricity production). **Decided 2026-10-05:** the demo uses this OJP value for train legs (issue #13).

## 5. Quirks and findings

| # | Finding | Consequence |
|---|---|---|
| 1 | All times are **UTC** (`Z`) | Convert to Europe/Zurich for display (12:02, not 10:02) |
| 2 | Durations are ISO 8601 (`PT56M`, `PT1H18M`) | Parse to minutes |
| 3 | `NumberOfResults` is a guideline (asked 3, got 4 in LIR) | Don't rely on the exact count |
| 4 | Stop IDs exist on two levels: `ch:1:sloid:3000` (station) and `ch:1:sloid:3000:500:31` (platform) | Compare on the station prefix |
| 5 | `IncludeFare=true` accepted, no fare in response | Prices via OJP Fare |
| 6 | Responses with geometry are large (TR with 2–3 results ≈ 550 KB) | Cache to `data/cache/` (gitignored) |
| 7 | Text has `xml:lang` (default `de`) | Request another language if needed |

Reference check (brief, trip 3): IC 8 Zürich HB 12:02 → Bern 12:58 – **matches**.

## 6. Local test files (not in Git)

In `data/cache/` (gitignored): `lir_zurich_hb.xml`, `trip_zurich_bern.xml`.
