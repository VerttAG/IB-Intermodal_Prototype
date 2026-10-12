# Geocoding – address → coordinates (swisstopo GeoAdmin API)

Status: derived from **real responses** on 2026-10-05 (trial). Field names below appear exactly like this in the responses.
Related: [routing.md](routing.md) · [PRD](../PRD.md) · PRD-1 (address input)

## 1. Overview

The customer types a start and a destination address; suggestions appear while typing; the chosen address is turned into coordinates for the trip engine.

| | |
|---|---|
| Provider | swisstopo GeoAdmin API (`api3.geo.admin.ch`) – official Swiss addresses |
| Auth | **None** – no key |
| Called from | The browser directly (`access-control-allow-origin: *`) for the suggestions; the chosen coordinates go to our server for the search |
| Answer time in the trial | 0.05 – 0.13 s |
| Covers | Switzerland only |
| Limits | Fair use – exact terms not checked yet (section 4) |

## 2. Request

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
| `attrs.lat` / `attrs.lon` | `46.94677` / `7.44419` | Coordinates (WGS84) | Passed to the trip engine |
| `attrs.origin` | `address` · `gg25` · `zipcode` | Kind of match | Tell an address from a whole municipality |

Trial: `Bundesplatz 3 Bern` → Bundesplatz 3, 3011 Bern · 46.94677, 7.44419.

## 3. Quirks

| # | Finding | Consequence |
|---|---|---|
| 1 | The search is fuzzy while typing: `Dorfstrasse Wettsw` returns addresses in Wettswil, but also unrelated near-matches (e.g. a municipality in Geneva); "Seestrasse 1 Küssnacht" first returned Küsnacht ZH | Show the list and let the customer pick; never take the first result silently |
| 2 | `label` contains HTML | Escape before display |
| 3 | Addresses outside Switzerland are not found | Message "address not found" (PRD-1) |

## 4. Decision and open point

- **Decided 2026-10-05:** swisstopo (fast, official, no key). Alternatives looked at: Nominatim (OpenStreetMap; no suggestions while typing on the public server), Photon (6–10 s in the trial), hosted services with a key (would need our backend). No "use my location" in Prototype 1, so no reverse geocoding (coordinates → address) is needed.
- **Open:** terms of use / fair-use limits of the GeoAdmin API – to read before the demo is shared with partners.
- **Privacy:** all trips are mock trips. Address and coordinates are used for the search only; they are not stored and never appear in the data link (PRD-5).
