"""Spike: does the AI model (Jev 1.13) choose sensible candidate stations? (PRD-8, open topics #11)

For each example journey:
  1. swisstopo: start / destination address -> coordinates
  2. OJP: railway stations within 8 km of each address; hubs (fixed list) within 25 km
  3. code: detour of every station = (start->station) + (station->destination) - (start->destination)
  4. Jev: per side "which hub?" and "which nearby station?" (top 2 by probability)
  5. compare with the code fallback (smallest detour) and print a table for Tim to judge

Run:  .venv\\Scripts\\python.exe spikes\\ai_station_choice.py
Keys from .env: OJP_API_KEY, OPENROUTER_API_KEY. Results are written to data/cache/spike_ai/ (gitignored).
"""
import datetime
import json
import math
import re
import time
from pathlib import Path

import httpx
from dotenv import dotenv_values
from lxml import etree

ENV = dotenv_values(".env")
OJP_KEY = ENV["OJP_API_KEY"]
OR_KEY = ENV.get("OPENROUTER_API_KEY") or ENV.get("OPEN_ROUTER_API_KEY")
CACHE = Path("data/cache/spike_ai")
CACHE.mkdir(parents=True, exist_ok=True)
NS = {"o": "http://www.vdv.de/ojp", "s": "http://www.siri.org.uk/siri"}

MODEL = "typesafe/jev-1.13"
NEARBY_RADIUS_M = 8000
HUB_RADIUS_KM = 25
THRESHOLD = 0.8
HUBS = ["Zürich HB", "Zürich Oerlikon", "Zürich Flughafen", "Winterthur", "Bern", "Olten", "Aarau", "Biel/Bienne",
        "Basel SBB", "Luzern", "Zug", "Arth-Goldau", "St. Gallen", "Chur", "Lausanne", "Genève", "Fribourg",
        "Bellinzona", "Lugano", "Visp", "Brig"]
JOURNEYS = [
    ("Dorfstrasse 1 Wettswil", "Bernstrasse 10 Ostermundigen"),
    ("Marktgasse 20 Winterthur", "Pilatusstrasse 5 Luzern"),
    ("Baselstrasse 1 Riehen", "Schaffhauserstrasse 1 Kloten"),
    ("Bankstrasse 1 Uster", "Bundesplatz 3 Bern"),
    ("Seestrasse 1 Küssnacht", "Piazza Collegiata 1 Bellinzona"),
    ("Seestrasse 100 Wädenswil", "Marktplatz 1 St. Gallen"),
]


def km(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    return 2 * 6371 * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))


def geocode(text):
    r = httpx.get("https://api3.geo.admin.ch/rest/services/api/SearchServer",
                  params={"searchText": text, "type": "locations", "origins": "address", "sr": 4326}, timeout=20)
    a = r.json()["results"][0]["attrs"]
    return re.sub(r"<[^>]+>", "", a["label"]), (a["lat"], a["lon"])


def ojp_lir(inner):
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<OJP xmlns="http://www.vdv.de/ojp" xmlns:siri="http://www.siri.org.uk/siri" version="2.0"><OJPRequest><siri:ServiceRequest>
<siri:RequestTimestamp>{now}</siri:RequestTimestamp><siri:RequestorRef>IB-Intermodal-Prototype</siri:RequestorRef>
<OJPLocationInformationRequest><siri:RequestTimestamp>{now}</siri:RequestTimestamp><siri:MessageIdentifier>LIR</siri:MessageIdentifier>
{inner}</OJPLocationInformationRequest></siri:ServiceRequest></OJPRequest></OJP>"""
    r = httpx.post("https://api.opentransportdata.swiss/ojp20", content=body.encode("utf-8"),
                   headers={"Authorization": f"Bearer {OJP_KEY}", "Content-Type": "application/xml"}, timeout=60)
    r.raise_for_status()
    out = []
    for p in etree.fromstring(r.content).iterfind(".//o:PlaceResult", NS):
        if "rail" not in [m.text for m in p.findall(".//o:Mode/o:PtMode", NS)]:
            continue
        out.append({"name": p.findtext(".//o:StopPlace/o:StopPlaceName/o:Text", namespaces=NS),
                    "ref": p.findtext(".//o:StopPlace/o:StopPlaceRef", namespaces=NS),
                    "pos": (float(p.findtext(".//o:GeoPosition/s:Latitude", namespaces=NS)),
                            float(p.findtext(".//o:GeoPosition/s:Longitude", namespaces=NS)))})
    return out


def rail_stations_near(pos):
    inner = (f"<InitialInput><GeoRestriction><Circle><Center><siri:Longitude>{pos[1]}</siri:Longitude>"
             f"<siri:Latitude>{pos[0]}</siri:Latitude></Center><Radius>{NEARBY_RADIUS_M}</Radius></Circle></GeoRestriction></InitialInput>"
             "<Restrictions><Type>stop</Type><Modes><Exclude>false</Exclude><PtMode>rail</PtMode></Modes>"
             "<NumberOfResults>400</NumberOfResults></Restrictions>")
    return ojp_lir(inner)


def hubs():
    f = CACHE / "hubs.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    out = []
    for name in HUBS:
        res = ojp_lir(f"<InitialInput><Name>{name}</Name></InitialInput>"
                      "<Restrictions><Type>stop</Type><NumberOfResults>5</NumberOfResults></Restrictions>")
        out.append(res[0])
        time.sleep(1.3)                       # stay under 50 calls/min
    f.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def options(side_pos, start, dest, hub_list):
    direct = km(start, dest)
    def enrich(s):
        detour = km(start, s["pos"]) + km(s["pos"], dest) - direct
        return {**s, "dist": km(side_pos, s["pos"]), "detour": detour,
                "where": "on the way to the destination" if detour < 0.15 * direct else "away from the destination"}
    hub_names = {h["name"] for h in hub_list}
    near = [enrich(s) for s in rail_stations_near(side_pos) if s["name"] not in hub_names]
    near = sorted(near, key=lambda s: s["dist"])[:10]
    hub_opts = [enrich(h) for h in hub_list if km(side_pos, h["pos"]) <= HUB_RADIUS_KM]
    return sorted(hub_opts, key=lambda s: s["detour"]), sorted(near, key=lambda s: s["detour"])


def describe(s, side, hub):
    return (f"{'Hub station with many long-distance trains' if hub else 'Railway station'}, "
            f"{s['dist']:.0f} km from the {side} address, {s['where']} (detour {s['detour']:.0f} km).")


def ask_jev(start_label, dest_label, sides, reverse=False):
    qs = {}
    for side, (hub_opts, near_opts) in sides.items():
        word = "start" if side == "start" else "destination"
        for kind, opts, is_hub in (("hub", hub_opts, True), ("station", near_opts, False)):
            if not opts:
                continue
            seq = list(reversed(opts)) if reverse else opts
            qs[f"{side}_{kind}"] = {
                "type": "choice",
                "instructions": (f"Which {'hub station' if is_hub else 'nearby railway station'} near the {word} address is the best "
                                 f"place to {'board' if side == 'start' else 'leave'} the train for this journey? Prefer stations on the way "
                                 f"and with good train connections; the customer is brought there by car."),
                "criteria": {s["name"]: describe(s, word, is_hub) for s in seq}}
    body = {"model": MODEL,
            "state": (f"A customer travels door to door from '{start_label}' to '{dest_label}' in Switzerland: a car to a railway "
                      f"station near the start, a train, then a car from a station near the destination."),
            "questions": qs}
    t0 = time.time()
    r = httpx.post("https://openrouter.ai/api/alpha/decisions", json=body, timeout=30,
                   headers={"Authorization": f"Bearer {OR_KEY}", "Content-Type": "application/json"})
    return r, time.time() - t0, body


def top(probs, n):
    return [k for k, _ in sorted(probs.items(), key=lambda kv: -kv[1])[:n]]


def main():
    if not OR_KEY:
        raise SystemExit("No OPENROUTER_API_KEY in .env")
    hub_list = hubs()
    report = []
    for s_text, d_text in JOURNEYS:
        (s_label, s_pos), (d_label, d_pos) = geocode(s_text), geocode(d_text)
        sides = {"start": options(s_pos, s_pos, d_pos, hub_list), "dest": options(d_pos, s_pos, d_pos, hub_list)}
        time.sleep(2.5)
        r, secs, body = ask_jev(s_label, d_label, sides)
        r2, _, _ = ask_jev(s_label, d_label, sides, reverse=True)
        entry = {"start": s_label, "dest": d_label, "direct_km": round(km(s_pos, d_pos), 1), "seconds": round(secs, 2),
                 "status": r.status_code, "request": body, "answer": r.json() if r.status_code == 200 else r.text,
                 "answer_reversed": r2.json() if r2.status_code == 200 else r2.text}
        report.append(entry)
        print(f"\n=== {s_label}  ->  {d_label}   ({entry['direct_km']} km, Jev {secs:.2f} s, HTTP {r.status_code})")
        if r.status_code != 200:
            print("   ", r.text[:400]); continue
        ans, ans2 = r.json()["answers"], r2.json().get("answers", {}) if r2.status_code == 200 else {}
        for side in ("start", "dest"):
            hub_opts, near_opts = sides[side]
            for kind, opts, n in (("hub", hub_opts, 1), ("station", near_opts, 2)):
                q = f"{side}_{kind}"
                if q not in ans:
                    print(f"   {q:14} no options"); continue
                a = ans[q]
                ai = top(a["probabilities"], n)
                code = [o["name"] for o in opts[:n]]
                same_rev = q in ans2 and top(ans2[q]["probabilities"], n) == ai
                flag = "" if a["confidence"] >= THRESHOLD else "  <- below threshold, code would decide"
                print(f"   {q:14} AI: {', '.join(ai):45} conf {a['confidence']:.2f}  | code: {', '.join(code):40}"
                      f" | same when reversed: {'yes' if same_rev else 'NO'}{flag}")
            print(f"   {'':14} options {side}: " + ", ".join(f"{o['name']} ({o['detour']:.0f})" for o in near_opts))
    out = CACHE / f"report_{datetime.datetime.now():%Y%m%d_%H%M}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nFull report: {out}")


if __name__ == "__main__":
    main()
