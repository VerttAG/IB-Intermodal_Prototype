"""OJP client – SBB data for the trip engine (PRD-6).

Four questions, answered from OJP 2.0 (timetable) and OJP Fare (prices):
  walk(a, b, when)                       walking time between an address and a station
  train(from_ref, to_ref, ready)         the train between two stations (trains only, PRD-8 rule)
  half_fare_price(trip)                  half-fare price, 2nd class, normal ticket preferred
  public_transport_only(a, b, when)      door to door by public transport (comparison card)

Places are either a stop reference ("ch:1:sloid:3000") or a position (lat, lon).
Times are datetimes with time zone; answers are in Swiss local time.

Try it locally:  .venv\\Scripts\\python.exe -m src.ojp
"""
from __future__ import annotations

import datetime as dt
import os
import re
from zoneinfo import ZoneInfo

import httpx
from lxml import etree

OJP_URL = "https://api.opentransportdata.swiss/ojp20"
FARE_URL = "https://api.opentransportdata.swiss/ojpfare"
O, S = "http://www.vdv.de/ojp", "http://www.siri.org.uk/siri"
NS = {"o": O, "s": S}
SWISS = ZoneInfo("Europe/Zurich")

TRANSFER_MIN = 8            # train leaves at least 8 min after arrival at the station
ARRIVAL_SLACK_MIN = 10      # fewest transfers among trains arriving within 10 min of the earliest
OPTIONS = 3                 # connections asked from OJP per question

_cache: dict = {}


# ---------- transport (replaced in the tests) ----------
def _post(url: str, xml: str, key_name: str) -> bytes:
    r = httpx.post(url, content=xml.encode("utf-8"), timeout=30,
                   headers={"Authorization": f"Bearer {os.environ[key_name]}", "Content-Type": "application/xml"})
    if url == OJP_URL:
        r.raise_for_status()
    return r.content


def _cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


# ---------- helpers ----------
def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local(text: str) -> dt.datetime:
    """OJP time (UTC, 'Z') -> Swiss local time."""
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(SWISS)


def minutes(duration: str) -> float:
    """ISO 8601 duration (PT1H5M30S) -> minutes."""
    h, m, s = (re.search(rf"(\d+){u}", duration) for u in "HMS")
    return (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0) + (int(s.group(1)) / 60 if s else 0)


def _place(p) -> str:
    if isinstance(p, str):
        return f"<PlaceRef><StopPlaceRef>{p}</StopPlaceRef><Name><Text>stop</Text></Name></PlaceRef>"
    return (f"<PlaceRef><GeoPosition><siri:Longitude>{p[1]}</siri:Longitude><siri:Latitude>{p[0]}</siri:Latitude>"
            f"</GeoPosition><Name><Text>address</Text></Name></PlaceRef>")


def _points(leg) -> list:
    return [[round(float(p.findtext("s:Latitude", namespaces=NS)), 5), round(float(p.findtext("s:Longitude", namespaces=NS)), 5)]
            for p in leg.iterfind(".//o:LinkProjection/o:Position", NS)]


# ---------- OJP 2.0: trips ----------
def _trip_request(origin, dest, when: dt.datetime, n: int) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OJP xmlns="{O}" xmlns:siri="{S}" version="2.0"><OJPRequest><siri:ServiceRequest>
<siri:RequestTimestamp>{_now()}</siri:RequestTimestamp><siri:RequestorRef>IB-Intermodal-Prototype</siri:RequestorRef>
<OJPTripRequest><siri:RequestTimestamp>{_now()}</siri:RequestTimestamp><siri:MessageIdentifier>TR</siri:MessageIdentifier>
<Origin>{_place(origin)}<DepArrTime>{_utc(when)}</DepArrTime></Origin><Destination>{_place(dest)}</Destination>
<Params><NumberOfResults>{n}</NumberOfResults><IncludeLegProjection>true</IncludeLegProjection></Params>
</OJPTripRequest></siri:ServiceRequest></OJPRequest></OJP>"""


def parse_trips(xml: bytes) -> list[dict]:
    """OJP trip answer -> list of trips with legs (train / walk / transfer)."""
    trips = []
    for trip in etree.fromstring(xml).iterfind(".//o:TripResult/o:Trip", NS):
        legs = []
        for leg in trip.iterfind("o:Leg", NS):
            co2_factor = float(leg.findtext("o:EmissionCO2/o:KilogramPerPersonKm", default="0", namespaces=NS))
            km = float(leg.findtext(".//o:TrackSection/o:Length", default="0", namespaces=NS) or 0) / 1000
            timed = leg.find("o:TimedLeg", NS)
            if timed is not None:
                legs.append({
                    "kind": "train" if timed.findtext(".//o:Service/o:Mode/o:PtMode", namespaces=NS) == "rail" else "other_pt",
                    "line": timed.findtext(".//o:PublishedServiceName/o:Text", namespaces=NS),
                    "from": timed.findtext("o:LegBoard/o:StopPointName/o:Text", namespaces=NS),
                    "to": timed.findtext("o:LegAlight/o:StopPointName/o:Text", namespaces=NS),
                    "dep": local(timed.findtext("o:LegBoard/o:ServiceDeparture/o:TimetabledTime", namespaces=NS)),
                    "arr": local(timed.findtext("o:LegAlight/o:ServiceArrival/o:TimetabledTime", namespaces=NS)),
                    "platform": timed.findtext("o:LegBoard/o:PlannedQuay/o:Text", namespaces=NS),
                    "km": round(km, 3), "co2_kg": round(km * co2_factor, 3), "route": _points(timed)})
            else:
                kind = "transfer" if leg.find("o:TransferLeg", NS) is not None else "walk"
                legs.append({"kind": kind, "minutes": round(minutes(leg.findtext("o:Duration", default="PT0M", namespaces=NS)), 1),
                             "km": round(km, 3), "route": _points(leg)})
        trips.append({"start": local(trip.findtext("o:StartTime", namespaces=NS)), "end": local(trip.findtext("o:EndTime", namespaces=NS)),
                      "transfers": int(trip.findtext("o:Transfers", default="0", namespaces=NS)), "legs": legs,
                      "xml": etree.tostring(trip, encoding="unicode")})
    return trips


def _trips(origin, dest, when, n=OPTIONS) -> list[dict]:
    key = ("trips", str(origin), str(dest), _utc(when), n)
    return _cached(key, lambda: parse_trips(_post(OJP_URL, _trip_request(origin, dest, when, n), "OJP_API_KEY")))


def choose_train(trips: list[dict], ready: dt.datetime) -> dict | None:
    """PRD-8 rule: trains only, leaving >= ready; earliest arrival, then fewest transfers within 10 min of it."""
    ok = [t for t in trips
          if any(l["kind"] == "train" for l in t["legs"])
          and not any(l["kind"] == "other_pt" for l in t["legs"])
          and min(l["dep"] for l in t["legs"] if l["kind"] == "train") >= ready]
    if not ok:
        return None
    earliest = min(t["end"] for t in ok)
    near = [t for t in ok if t["end"] <= earliest + dt.timedelta(minutes=ARRIVAL_SLACK_MIN)]
    return min(near, key=lambda t: (t["transfers"], t["end"]))


def train(from_ref: str, to_ref: str, arrival_at_station: dt.datetime) -> dict | None:
    """The train between two stations for someone arriving at the station at the given time."""
    ready = arrival_at_station + dt.timedelta(minutes=TRANSFER_MIN)
    return choose_train(_trips(from_ref, to_ref, ready), ready)


def walk(a, b, when: dt.datetime) -> dict | None:
    """Walking only, between an address and a station: {'minutes', 'km', 'route'} or None."""
    for t in _trips(a, b, when):
        if t["legs"] and all(l["kind"] == "walk" for l in t["legs"]):
            return {"minutes": sum(l["minutes"] for l in t["legs"]), "km": sum(l["km"] for l in t["legs"]),
                    "route": [p for l in t["legs"] for p in l["route"]]}
    return None


def public_transport_only(a, b, when: dt.datetime) -> dict | None:
    """Door to door by public transport (any mode) – the first connection OJP offers, with its half-fare price."""
    trips = _trips(a, b, when, n=1)
    if not trips:
        return None
    return {**trips[0], "price": half_fare_price(trips[0])}


# ---------- OJP Fare ----------
def _fare_request(trip_xml: str) -> str:
    trip = etree.fromstring(trip_xml)
    for tag in ("LegTrack", "LegProjection"):                       # geometry is not needed for the price
        for el in trip.findall(f".//o:{tag}", NS):
            el.getparent().remove(el)
    trip_s = re.sub(r'\sxmlns(:\w+)?="[^"]+"', "", etree.tostring(trip, encoding="unicode"))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OJP xmlns="{O}" xmlns:siri="{S}" version="2.0"><OJPRequest><siri:ServiceRequest>
<siri:RequestTimestamp>{_now()}</siri:RequestTimestamp><siri:RequestorRef>IB-Intermodal-Prototype</siri:RequestorRef>
<OJPFareRequest><siri:RequestTimestamp>{_now()}</siri:RequestTimestamp><TripFareRequest>{trip_s}</TripFareRequest>
<Params><FareAuthorityFilter>ch:1:NOVA</FareAuthorityFilter><PassengerCategory>Adult</PassengerCategory><FareClass>secondClass</FareClass>
<Traveller><PassengerCategory>Adult</PassengerCategory><EntitlementProducts><EntitlementProduct><FareAuthorityRef>NOVA</FareAuthorityRef>
<EntitlementProductRef>HTA</EntitlementProductRef><EntitlementProductName>Halbtax</EntitlementProductName></EntitlementProduct>
</EntitlementProducts></Traveller></Params></OJPFareRequest></siri:ServiceRequest></OJPRequest></OJP>"""


def parse_fare(xml: bytes) -> dict | None:
    """OJP Fare answer -> {'price', 'product'} for 2nd class (normal ticket preferred), or None."""
    try:
        root = etree.fromstring(xml)
    except etree.XMLSyntaxError:
        return None
    second = [{"product": (fp.findtext(f"{{{O}}}FareProductName") or "").strip(), "price": float(fp.findtext(f"{{{O}}}Price"))}
              for fp in root.iter(f"{{{O}}}FareProduct") if (fp.findtext(f"{{{O}}}FareClass") or "").strip() == "secondClass"]
    if not second:
        return None
    normal = [p for p in second if p["product"] == "Streckenbillett"]
    return min(normal or second, key=lambda p: p["price"])


def half_fare_price(trip: dict) -> dict | None:
    """Half-fare price of a trip; one retry if NOVA gives none. None -> the trip engine estimates (PRD-8).

    The trip must be sent exactly as OJP returned it (only the geometry is removed): a shortened trip
    made NOVA answer "There was no valid NOVA response" in the tests.
    """
    def ask():
        req = _fare_request(trip["xml"])
        return parse_fare(_post(FARE_URL, req, "OJP_FARE_API_KEY")) or parse_fare(_post(FARE_URL, req, "OJP_FARE_API_KEY"))
    return _cached(("fare", trip["xml"]), ask)


if __name__ == "__main__":                 # quick local try with real data
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    at = dt.datetime(2026, 10, 13, 8, 30, tzinfo=SWISS)
    t = train("ch:1:sloid:3000", "ch:1:sloid:7000", at)
    print("train Zürich HB -> Bern, at station 08:30:",
          [(l["line"], f"{l['dep']:%H:%M}", f"{l['arr']:%H:%M}", l["platform"], l["km"], l["co2_kg"]) for l in t["legs"] if l["kind"] == "train"],
          "transfers", t["transfers"], "| price", half_fare_price(t))
    print("walk Winterthur Marktgasse -> station:", {k: v for k, v in walk((47.4993, 8.7290), "ch:1:sloid:6000", at).items() if k != "route"})
