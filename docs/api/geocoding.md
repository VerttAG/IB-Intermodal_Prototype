# Geocoding – address ↔ coordinates (swisstopo GeoAdmin API)

Status: derived from **real responses** on 2026-10-05 (trial). Field names below appear exactly like this in the responses.
Related: [ojp20.md](ojp20.md) · [ojpfare.md](ojpfare.md) · [PRD](../PRD.md) · [CTO meeting](../cto-meeting.md) (T3 row 1)

## 1. Overview

Two directions, two different requests:

| Direction | Name | Question it answers | Needed for |
|---|---|---|---|
| Address → coordinates | **Geocoding** (forward) | "Where is *Bundesplatz 3, Bern*?" | The customer types an address; we pass latitude/longitude to the Vertt API (story 2) |
| Coordinates → address | **Reverse geocoding** | "Which address is at 46.9468, 7.4442?" | Only if the customer starts from a position instead of an address: "use my location" or a tap on the map |

| | |
|---|---|
| Provider | swisstopo GeoAdmin API (`api3.geo.admin.ch`) – official Swiss addresses |
| Auth | **None** – no key |
| Called from | The browser directly (`access-control-allow-origin: *`), so a typed address never reaches our own server |
| Answer time in the trial | 0.05 – 0.13 s |
| Covers | Switzerland only |
| Limits | Fair use – exact terms **not yet checked**, see section 5 |

## 2. Address → coordinates (`SearchServer`)

```
GET https://api3.geo.admin.ch/rest/services/api/SearchServer
      ?searchText=Bundesplatz 3 Bern
      &type=locations
      &origins=address          (also possible: gg25 = municipality, zipcode)
      &sr=4326                  (answer in latitude/longitude, WGS84)
      &limit=5
```

Response: `results[]`, best match first.

| Path | Example | Meaning | Use in project |
|---|---|---|---|
| `attrs.label` | `Bundesplatz 3 <b>3011 Bern</b>` | Display text – **contains HTML** (`<b>`) | Suggestion list; strip or escape the tags |
| `attrs.lat` / `attrs.lon` | `46.94677` / `7.44419` | Coordinates (WGS84) | Passed to the Vertt API |
| `attrs.origin` | `address` · `gg25` · `zipcode` | Kind of match | Tell an address from a whole municipality |
| `attrs.detail` | `bundesplatz 3 3011 bern 351 bern ch be` | Search text incl. municipality and canton | – |
| `attrs.featureId` | `2242547_0` | Building ID (EGID) + entrance | Not stored |

Works while typing: `Dorfstrasse Wettsw` already returns addresses in Wettswil – but also unrelated near-matches (e.g. a municipality in Geneva). Show the list and let the customer pick; do not take the first result silently.

## 3. Coordinates → address (`MapServer/identify`)

GeoAdmin has no dedicated reverse-geocoding request. The way to do it is to ask which buildings of the federal building register lie around a point:

```
GET https://api3.geo.admin.ch/rest/services/api/MapServer/identify
      ?geometryType=esriGeometryPoint
      &geometry=7.444192,46.946773         (longitude,latitude – this order)
      &sr=4326
      &layers=all:ch.bfs.gebaeude_wohnungs_register
      &mapExtent=7.44346,46.94627,7.44492,46.94727   (a box of about 100 m around the point)
      &imageDisplay=100,100,96
      &tolerance=30                        (search radius: with the box above, about 30 m)
      &returnGeometry=true&geometryFormat=geojson
```

Response: `results[]` – **not sorted by distance**; pick the nearest yourself.

| Path | Example | Meaning |
|---|---|---|
| `properties.strname_deinr` | `Bundesplatz 3` | Street and house number |
| `properties.dplz4` / `dplzname` | `3011` / `Bern` | Postcode and town |
| `properties.ggdename` | `Bern` | Municipality |
| `geometry.coordinates` | `[7.44419, 46.94677]` | Position of the building |

## 4. Quirks and findings

| # | Finding | Consequence |
|---|---|---|
| 1 | The search radius is given in **pixels of an imaginary map** (`mapExtent` + `imageDisplay` + `tolerance`). With a careless `mapExtent` the request returned 201 buildings from all over Switzerland | Always send a small box around the point, as in section 3 |
| 2 | Reverse results are unsorted | Calculate the distance and take the nearest |
| 3 | A point with no building within the radius returns nothing – Zürich HB main hall: 0 results at 30 m | Widen the radius step by step, or fall back to the municipality |
| 4 | Outside Switzerland: 0 results (tested: Konstanz) | "Area not covered" (story 2) |
| 5 | Order is `longitude,latitude` in `geometry`, but `lat`/`lon` are named in the search answer | Easy to swap – test with a known address |
| 6 | `label` contains HTML | Escape before display |
| 7 | Forward search is fuzzy while typing | Customer picks from the list |

Trial results:

| Request | Input | Result |
|---|---|---|
| Forward | `Bundesplatz 3 Bern` | Bundesplatz 3, 3011 Bern · 46.94677, 7.44419 |
| Reverse | 46.946773, 7.444192 | Bundesplatz 3, 3011 Bern · distance 0 m |
| Reverse | Zürich HB main hall | no building within 30 m |
| Reverse | point in Kilchberg | 4 buildings within 30 m, nearest at 6 m |
| Reverse | Konstanz (Germany) | nothing |

## 5. Options compared

Tried on 2026-10-05 with the same address (Bundesplatz 3, Bern), both directions. "Not tried" = from the provider's description only.

| Option | Key | Address → coordinates | Coordinates → address | Answer time | Notes |
|---|---|---|---|---|---|
| **swisstopo GeoAdmin** (sections 2–3) | none | ✅ official address, suggestions while typing | ✅ but indirect: nearest registered building; nothing where no building is near | 0.05 – 0.13 s | Switzerland only. Recommended for typing an address |
| **Nominatim** (OpenStreetMap, public server) | none | ✅ found the building, as a point of interest ("Bundeshaus") | ✅ real reverse request; also answered inside Zürich HB, where swisstopo found nothing | 0.8 – 1.3 s | Worldwide. Public server: at most 1 request per second and **no suggestions while typing** (usage policy – to re-read before use) |
| **Photon** (OpenStreetMap, public server by Komoot) | none | ✅ made for suggestions while typing | ⚠️ returned a monument, not the address | 6.5 – 9.8 s in the trial | Too slow on the day of the trial; public server without guarantee |
| Hosted services with a key: OpenRouteService, Geoapify, LocationIQ, MapTiler, Mapbox, Google | yes | not tried | not tried | – | A key must not be in the browser → needs our backend. Google restricts storing results. Vertt's own route data is in Google format |
| OJP 2.0 `LocationInformationRequest` | yes (have one) | not tried – address support to verify (CTO meeting T3) | not tried | – | Already used for stations; needs our backend to hide the key |
| Run it ourselves: Nominatim or Photon with the Swiss map extract, or the official list of Swiss building addresses with a local search | none | not tried | not tried | – | No outside service and no limits, but something to install, host and update |

All three public services tried can be called from the browser directly.

**Decided 2026-10-05:** swisstopo for the address the customer types (fast, official, no key). Only if "use my location" is wanted: Nominatim for that single coordinates → address request, because it also answers where no building is near.

## 6. Open points

- **Terms of use / fair-use limits** of the GeoAdmin API were not checked in the trial. To verify before the demo is shared with partners.
- **Privacy:** a typed address and its exact coordinates are personal data. The address stays in the browser (direct call to swisstopo). Before coordinates go to the Vertt API they can be rounded to 3 decimals (about 100 m) – enough to find the nearest place Vertt serves. Nothing of it is stored (stories 2, 21).
- Is reverse geocoding needed at all in Prototype 1? Only with "use my location" or picking a point on the map – see PRD-1.
