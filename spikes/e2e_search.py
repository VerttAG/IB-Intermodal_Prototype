"""Spike: one real trip search end to end, as specified in PRD-8 (no app, no Vercel).

swisstopo -> tier rule (config/hubs.yaml) -> Valhalla / walk -> OJP first train -> OJP Fare (half-fare)
-> totals -> labels, plus the comparison cards "Vertt only" and "Public transport only".
Measures total time and calls per API; prints the OJP Fare products (normal vs. saver ticket).

Run:  .venv\\Scripts\\python.exe spikes\\e2e_search.py
Keys from .env: OJP_API_KEY, OJP_FARE_API_KEY. Raw answers: data/cache/e2e/ (gitignored).
"""
import copy
import datetime as dt
import json
import math
import random
import re
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import yaml
from dotenv import dotenv_values
from lxml import etree

ENV = dotenv_values(".env")
O, S = "http://www.vdv.de/ojp", "http://www.siri.org.uk/siri"
NS = {"o": O, "s": S}
CACHE = Path("data/cache/e2e")
CACHE.mkdir(parents=True, exist_ok=True)
HUBS = yaml.safe_load(open("config/hubs.yaml", encoding="utf-8"))["hubs"]
CARS = yaml.safe_load(open("config/car_pool.yaml", encoding="utf-8"))["cars"]
TZ = dt.timezone(dt.timedelta(hours=2))          # Swiss summer time until 25.10.2026
WALK_KM, HUB_RADIUS_KM, MIN_TRIP_KM, TRANSFER_MIN = 1.0, 25, 10, 8
WAIT_START, WAIT_DEST = 5, 2
ARRIVAL_SLACK_MIN = 10          # train choice: arrive at most 10 min after the earliest, then fewest transfers
HALF_FARE_CHF_PER_KM = 0.22     # fallback if no train of the search could be priced

JOURNEYS = [
    ("Dorfstrasse 1 Wettswil", "Bernstrasse 10 Ostermundigen", "2026-10-13 08:00"),
    ("Marktgasse 20 Winterthur", "Bundesplatz 3 Bern", "2026-10-13 08:00"),
]

CALLS = Counter()
LOCK = threading.Lock()
http = httpx.Client(timeout=60)


def count(api):
    with LOCK:
        CALLS[api] += 1


def km(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    return 2 * 6371 * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))


def iso_minutes(d):                         # PT1H5M30S -> minutes
    h, m, s = (re.search(rf"(\d+){u}", d) for u in "HMS")
    return (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0) + (int(s.group(1)) / 60 if s else 0)


def utc(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(TZ)


# ---------- partner calls ----------
def geocode(text):
    count("swisstopo")
    r = http.get("https://api3.geo.admin.ch/rest/services/api/SearchServer",
                 params={"searchText": text, "type": "locations", "origins": "address", "sr": 4326})
    a = r.json()["results"][0]["attrs"]
    return re.sub(r"<[^>]+>", "", a["label"]), (a["lat"], a["lon"])


def valhalla(a, b):
    count("Valhalla")
    r = http.post("https://valhalla1.openstreetmap.de/route",
                  json={"locations": [{"lat": a[0], "lon": a[1]}, {"lat": b[0], "lon": b[1]}], "costing": "auto"})
    r.raise_for_status()
    s = r.json()["trip"]["summary"]
    return s["length"], s["time"] / 60


def ojp(body, name):
    count("OJP")
    now = utc(dt.datetime.now(dt.timezone.utc))
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OJP xmlns="{O}" xmlns:siri="{S}" version="2.0"><OJPRequest><siri:ServiceRequest>
<siri:RequestTimestamp>{now}</siri:RequestTimestamp><siri:RequestorRef>IB-Intermodal-Prototype</siri:RequestorRef>
<OJPTripRequest><siri:RequestTimestamp>{now}</siri:RequestTimestamp><siri:MessageIdentifier>{name}</siri:MessageIdentifier>
{body}</OJPTripRequest></siri:ServiceRequest></OJPRequest></OJP>"""
    r = http.post("https://api.opentransportdata.swiss/ojp20", content=xml.encode("utf-8"),
                  headers={"Authorization": f"Bearer {ENV['OJP_API_KEY']}", "Content-Type": "application/xml"})
    r.raise_for_status()
    (CACHE / f"{name}.xml").write_bytes(r.content)
    return etree.fromstring(r.content)


def place(p, label):
    if isinstance(p, str):
        return f"<PlaceRef><StopPlaceRef>{p}</StopPlaceRef><Name><Text>{label}</Text></Name></PlaceRef>"
    return f"<PlaceRef><GeoPosition><siri:Longitude>{p[1]}</siri:Longitude><siri:Latitude>{p[0]}</siri:Latitude></GeoPosition><Name><Text>{label}</Text></Name></PlaceRef>"


def trips(origin, dest, when, name, n=3, geometry=False):
    params = f"<NumberOfResults>{n}</NumberOfResults>" + ("<IncludeLegProjection>true</IncludeLegProjection>" if geometry else "")
    root = ojp(f"<Origin>{place(origin, 'A')}<DepArrTime>{utc(when)}</DepArrTime></Origin>"
               f"<Destination>{place(dest, 'B')}</Destination><Params>{params}</Params>", name)
    return root.findall(".//o:TripResult/o:Trip", NS)


def trip_info(trip):
    legs = []
    for leg in trip.findall("o:Leg", NS):
        t = leg.find("o:TimedLeg", NS)
        co2 = float(leg.findtext("o:EmissionCO2/o:KilogramPerPersonKm", default="0", namespaces=NS))
        length = float(leg.findtext(".//o:Length", default="0", namespaces=NS) or 0) / 1000
        if t is not None:
            legs.append({"kind": "train", "line": t.findtext(".//o:PublishedServiceName/o:Text", namespaces=NS),
                         "mode": t.findtext(".//o:Mode/o:PtMode", namespaces=NS),
                         "dep": local(t.findtext("o:LegBoard/o:ServiceDeparture/o:TimetabledTime", namespaces=NS)),
                         "arr": local(t.findtext("o:LegAlight/o:ServiceArrival/o:TimetabledTime", namespaces=NS)),
                         "platform": t.findtext("o:LegBoard/o:PlannedQuay/o:Text", namespaces=NS), "km": length, "co2": co2 * length})
        else:
            legs.append({"kind": "walk", "min": iso_minutes(leg.findtext("o:Duration", default="PT0M", namespaces=NS))})
    return {"start": local(trip.findtext("o:StartTime", namespaces=NS)), "end": local(trip.findtext("o:EndTime", namespaces=NS)),
            "transfers": int(trip.findtext("o:Transfers", default="0", namespaces=NS)), "legs": legs, "xml": trip}


def first_train(origin_ref, dest_ref, ready, name):
    """Train-only trip leaving >= ready: earliest arrival, but fewest transfers among those within 10 min of it."""
    ok = []
    for t in map(trip_info, trips(origin_ref, dest_ref, ready, name, geometry=True)):
        trains = [l for l in t["legs"] if l["kind"] == "train"]
        if trains and trains[0]["dep"] >= ready and all(l["mode"] == "rail" for l in trains):
            ok.append(t)
    if not ok:
        return None
    earliest = min(t["end"] for t in ok)
    near = [t for t in ok if t["end"] <= earliest + dt.timedelta(minutes=ARRIVAL_SLACK_MIN)]
    return min(near, key=lambda t: (t["transfers"], t["end"]))


def walk(a, b, when, name):
    """Walk from a position to a stop (or back): OJP trip that consists of walking only."""
    for t in map(trip_info, trips(a, b, when, name, n=3)):
        if t["legs"] and all(l["kind"] == "walk" for l in t["legs"]):
            return sum(l["min"] for l in t["legs"])
    return None


def half_fare(trip_xml, name):
    price, info = _half_fare(trip_xml, name)
    if price is None:                                   # NOVA sometimes fails – one retry
        time.sleep(1)
        price, info = _half_fare(trip_xml, name + "_retry")
        info = ("retry: " if price is not None else "failed twice: ") + info
    return price, info


def _half_fare(trip_xml, name):
    count("OJP Fare")
    trip = copy.deepcopy(trip_xml)
    for tag in ("LegTrack", "LegProjection"):
        for el in trip.findall(f".//o:{tag}", NS):
            el.getparent().remove(el)
    trip_s = re.sub(r'\sxmlns(:\w+)?="[^"]+"', "", etree.tostring(trip, encoding="unicode"))
    now = utc(dt.datetime.now(dt.timezone.utc))
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OJP xmlns="{O}" xmlns:siri="{S}" version="2.0"><OJPRequest><siri:ServiceRequest>
<siri:RequestTimestamp>{now}</siri:RequestTimestamp><siri:RequestorRef>IB-Intermodal-Prototype</siri:RequestorRef>
<OJPFareRequest><siri:RequestTimestamp>{now}</siri:RequestTimestamp><TripFareRequest>{trip_s}</TripFareRequest>
<Params><FareAuthorityFilter>ch:1:NOVA</FareAuthorityFilter><PassengerCategory>Adult</PassengerCategory><FareClass>secondClass</FareClass>
<Traveller><PassengerCategory>Adult</PassengerCategory><EntitlementProducts><EntitlementProduct><FareAuthorityRef>NOVA</FareAuthorityRef>
<EntitlementProductRef>HTA</EntitlementProductRef><EntitlementProductName>Halbtax</EntitlementProductName></EntitlementProduct></EntitlementProducts></Traveller>
</Params></OJPFareRequest></siri:ServiceRequest></OJPRequest></OJP>"""
    r = http.post("https://api.opentransportdata.swiss/ojpfare", content=xml.encode("utf-8"),
                  headers={"Authorization": f"Bearer {ENV['OJP_FARE_API_KEY']}", "Content-Type": "application/xml"})
    (CACHE / f"{name}.xml").write_bytes(r.content)
    if r.status_code != 200:
        err = re.search(rb"<[^>]*ErrorText>([^<]+)<", r.content)
        return None, f"HTTP {r.status_code} {err.group(1).decode() if err else ''}"
    prods = [{"name": (fp.findtext(f"{{{O}}}FareProductName") or "").strip(), "price": float(fp.findtext(f"{{{O}}}Price")),
              "cls": (fp.findtext(f"{{{O}}}FareClass") or "").strip()} for fp in etree.fromstring(r.content).iter(f"{{{O}}}FareProduct")]
    second = [p for p in prods if p["cls"] == "secondClass"]
    if not second:
        return None, "no 2nd class product"
    normal = [p for p in second if "Strecken" in p["name"]]
    pick = min(normal or second, key=lambda p: p["price"])
    return pick["price"], " / ".join(f"{p['name']} {p['price']:.2f}" for p in second)


# ---------- engine ----------
def candidates(pos, start, dest):
    direct = km(start, dest)
    rows = [dict(h, dist=km(pos, (h["lat"], h["lon"])),
                 det=km(start, (h["lat"], h["lon"])) + km((h["lat"], h["lon"]), dest) - direct) for h in HUBS]
    best = lambda rs: min(rs, key=lambda r: r["dist"] + r["det"])
    t1 = [r for r in rows if r["tier"] == 1 and r["dist"] <= HUB_RADIUS_KM]
    out = [best(t1) if t1 else min((r for r in rows if r["tier"] == 1), key=lambda r: r["dist"])]
    for tier in (2, 3):
        c = [r for r in rows if r["tier"] == tier and r["dist"] <= HUB_RADIUS_KM]
        if c and best(c)["dist"] < min(o["dist"] for o in out):
            out.append(best(c))
    return out


def vertt_leg(a, b, rng):
    dist, minutes = valhalla(a, b)
    car = rng.choice(CARS)
    price = max(10.0, 3 + 1.8 * dist + 0.3 * minutes)
    return {"kind": "vertt", "km": dist, "min": minutes, "price": price, "car": f"{car['make']} {car['model']} {car['year']}",
            "g": car["co2_g_per_km"], "co2": dist * car["co2_g_per_km"] / 1000}


r05 = lambda x: round(x * 20) / 20


def search(s_text, d_text, depart):
    rng = random.Random(42)
    tag = re.sub(r"\W+", "", s_text)[:12]
    t0 = time.time()
    with ThreadPoolExecutor(12) as pool:
        (s_label, s_pos), (d_label, d_pos) = pool.map(geocode, [s_text, d_text])
        print(f"\n=== {s_label}  ->  {d_label}   ({km(s_pos, d_pos):.0f} km straight, depart {depart:%a %d.%m %H:%M})")
        if km(s_pos, d_pos) < MIN_TRIP_KM:
            print("    Trip not suitable for intermodal journey"); return
        cs, cd = candidates(s_pos, s_pos, d_pos), candidates(d_pos, s_pos, d_pos)
        print("    start stations:", ", ".join(f"{c['name']} (T{c['tier']}, {c['dist']:.1f} km)" for c in cs))
        print("    dest  stations:", ", ".join(f"{c['name']} (T{c['tier']}, {c['dist']:.1f} km)" for c in cd))

        # round 1: first legs (time known), last-leg distances, comparisons
        def first_leg(c):
            pos = (c["lat"], c["lon"])
            if c["dist"] <= WALK_KM:
                m = walk(s_pos, c["stop_ref"], depart, f"walk_start_{c['name']}") or c["dist"] / 4.5 * 60
                return {"kind": "walk", "min": m, "price": 0, "co2": 0, "arr": depart + dt.timedelta(minutes=m)}
            leg = vertt_leg(s_pos, pos, rng)
            leg["pick"] = depart + dt.timedelta(minutes=WAIT_START)
            leg["arr"] = leg["pick"] + dt.timedelta(minutes=leg["min"])
            return leg

        def last_leg(c):
            if c["dist"] <= WALK_KM:
                return {"kind": "walk", "min": None, "price": 0, "co2": 0, "stop": c["stop_ref"]}
            return vertt_leg((c["lat"], c["lon"]), d_pos, rng)

        f_first = {c["name"]: pool.submit(first_leg, c) for c in cs}
        f_last = {c["name"]: pool.submit(last_leg, c) for c in cd}
        f_vo = pool.submit(vertt_leg, s_pos, d_pos, rng)
        f_pt = pool.submit(lambda: [trip_info(t) for t in trips(s_pos, d_pos, depart, f"pt_only_{tag}", n=1, geometry=True)])
        first = {k: f.result() for k, f in f_first.items()}
        last = {k: f.result() for k, f in f_last.items()}

        # round 2: first train per station pair
        combos = [(a, b) for a in cs for b in cd if a["stop_ref"] != b["stop_ref"]]
        f_tr = {(a["name"], b["name"]): pool.submit(first_train, a["stop_ref"], b["stop_ref"],
                                                     first[a["name"]]["arr"] + dt.timedelta(minutes=TRANSFER_MIN),
                                                     f"train_{tag}_{a['name']}_{b['name']}".replace("/", "-")) for a, b in combos}
        trains = {k: f.result() for k, f in f_tr.items()}

        # round 3: half-fare prices (+ comparison price), walk at the destination
        f_fare = {k: pool.submit(half_fare, t["xml"], f"fare_{tag}_{k[0]}_{k[1]}".replace("/", "-")) for k, t in trains.items() if t}
        pt = f_pt.result()
        f_pt_fare = pool.submit(half_fare, pt[0]["xml"], f"fare_pt_only_{tag}") if pt else None
        fares = {k: f.result() for k, f in f_fare.items()}
        pt_fare = f_pt_fare.result() if f_pt_fare else (None, "no trip")
        for k, t in trains.items():
            l = last[k[1]]
            if t and l["kind"] == "walk" and l["min"] is None:
                c = next(c for c in cd if c["name"] == k[1])
                l["min"] = walk(c["stop_ref"], d_pos, t["end"], f"walk_dest_{c['name']}") or c["dist"] / 4.5 * 60
        vo = f_vo.result()
    secs = time.time() - t0

    # totals and labels
    train_km = lambda t: sum(x["km"] for x in t["legs"] if x["kind"] == "train")
    priced = [(fares[k][0], train_km(t)) for k, t in trains.items() if t and fares.get(k, (None,))[0] and train_km(t)]
    rate = sum(p for p, _ in priced) / sum(k for _, k in priced) if priced else HALF_FARE_CHF_PER_KM
    for k, t in trains.items():
        if t and fares.get(k, (None,))[0] is None:
            fares[k] = (r05(rate * train_km(t)), f"ESTIMATED {rate:.3f} CHF/km ({fares[k][1]})")
    if pt and pt_fare[0] is None:
        pt_fare = (r05(rate * train_km(pt[0])), f"ESTIMATED ({pt_fare[1]})")
    offers = []
    for (a, b), t in trains.items():
        if not t:
            print(f"    skipped {a} -> {b}: no train"); continue
        f, l = first[a], last[b]
        end = t["end"] + dt.timedelta(minutes=(WAIT_DEST if l["kind"] == "vertt" else 0) + (l["min"] or 0))
        half = fares[(a, b)][0]
        legs_price = [r05(f["price"]), half, r05(l["price"])]
        offers.append({"via": f"{a} -> {b}", "dep": depart, "end": end, "half": half, "first": f, "last": l, "train": t,
                       "price_half": r05(sum(legs_price)), "co2": f["co2"] + sum(x["co2"] for x in t["legs"] if x["kind"] == "train") + l["co2"],
                       "fare_products": fares[(a, b)][1]})
    if not offers:
        print("    no trip found"); return
    lab = {}
    for name, key in (("Fastest", lambda o: (o["end"], o["price_half"])), ("Cheapest", lambda o: (o["price_half"], o["end"])),
                      ("Greenest", lambda o: (o["co2"], o["end"]))):
        lab.setdefault(min(offers, key=key)["via"], []).append(name)

    print(f"    {len(offers)} trips built, {len(lab)} shown – search took {secs:.1f} s")
    for o in sorted(offers, key=lambda o: o["end"]):
        f, l, tr = o["first"], o["last"], [x for x in o["train"]["legs"] if x["kind"] == "train"]
        tag = "/".join(lab.get(o["via"], [])) or "(not shown)"
        first_s = f"Vertt {f['km']:.1f} km {f['min']:.0f} min CHF {f['price']:.2f} [{f['car']}, {f['g']} g/km]" if f["kind"] == "vertt" else f"walk {f['min']:.0f} min"
        last_s = f"Vertt {l['km']:.1f} km {l['min']:.0f} min CHF {l['price']:.2f} [{l['car']}]" if l["kind"] == "vertt" else f"walk {l['min']:.0f} min"
        print(f"    - {tag:18} {o['via']:32} {o['dep']:%H:%M}-{o['end']:%H:%M}  CHF {o['price_half']:6.2f} (half-fare)  CO2 {o['co2']:.1f} kg")
        print(f"        {first_s}  |  train {' + '.join(f'{x['line']} {x['dep']:%H:%M}-{x['arr']:%H:%M} pl.{x['platform']}' for x in tr)}"
              f" half-fare CHF {o['half']:.2f}  |  {last_s}")
        print(f"        OJP Fare products: {o['fare_products']}")
    print(f"    comparison Vertt only: {vo['km']:.0f} km {vo['min']:.0f} min CHF {r05(vo['price']):.2f}, CO2 {vo['co2']:.1f} kg")
    if pt:
        p = pt[0]
        print(f"    comparison public transport only: {p['start']:%H:%M}-{p['end']:%H:%M}, {p['transfers']} transfers, "
              f"half-fare {pt_fare[0]}, CO2 {sum(x['co2'] for x in p['legs'] if x['kind'] == 'train'):.1f} kg  [{pt_fare[1]}]")


if __name__ == "__main__":
    for s_text, d_text, when in JOURNEYS:
        CALLS.clear()
        search(s_text, d_text, dt.datetime.fromisoformat(when).replace(tzinfo=TZ))
        print("    calls:", dict(CALLS))
