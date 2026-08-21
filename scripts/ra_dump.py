#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ra_dump.py -- Resident Advisori Eesti uritused GraphQL-ist snapshotiks.

Taust (21.08.2026 audit): RA (ra.co/events/ee/all) on klubi-poole POHIALLIKAS,
mida sweep-agent seni sirvis Chrome'is lehekulje kaupa (?startDate=... nadalate
kaupa) -- sweepi kalleim ja aeglaseim osa. ra.co/graphql on avalik ja vastab
serverile probleemita (kontrollitud 21.08: ping, introspektsioon, listing).

MIDA: tombab area 184 (All Estonia) uritused tanasest +60 paeva ja kirjutab
sweep/ra_snapshot.json. Jookseb iga paev Andmekorjes (update.yml) -- reedene
sweep LOEB snapshoti failist ja kulastab RA-d Chrome'is ainult siis, kui
snapshot on vana voi kahtlane. See EI lisa midagi automaatselt saidile:
kirjete valik (skoop! peavoolu kommertsklubid valja) ja rikastamine jaab
sweep-agendi/inimese otsustada nagu enne.

Kasutus: python scripts/ra_dump.py   (kirjutab sweep/ra_snapshot.json)
"""
import json, sys, time, urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALJUND = ROOT / "sweep" / "ra_snapshot.json"
URL = "https://ra.co/graphql"
AREA_ALL_ESTONIA = 184   # country(urlCode:"ee") -> areas: All=184, Tallinn=566
AKEN_PAEVI = 60
HDR = {"User-Agent": "Mozilla/5.0 (compatible; skene.info korje; +https://www.skene.info)",
       "Content-Type": "application/json", "Referer": "https://ra.co/events/ee/all"}

Q = """
query($f: FilterInputDtoInput, $ps: Int, $p: Int) {
  eventListings(filters: $f, pageSize: $ps, page: $p) {
    totalResults
    data { listingDate
      event { id title date startTime endTime contentUrl isTicketed
        venue { name contentUrl area { name } }
        artists { name }
        genres { name }
      }
    }
  }
}"""


def post(variables):
    payload = {"query": Q, "variables": variables}
    r = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=HDR)
    with urllib.request.urlopen(r, timeout=30) as resp:
        d = json.loads(resp.read().decode("utf-8", "replace"))
    if "errors" in d:
        raise RuntimeError("GraphQL viga: %s" % json.dumps(d["errors"])[:300])
    return d["data"]["eventListings"]


def main():
    algus = date.today().isoformat()
    lopp = (date.today() + timedelta(days=AKEN_PAEVI)).isoformat()
    f = {"areas": {"eq": AREA_ALL_ESTONIA},
         "listingDate": {"gte": algus, "lte": lopp}}
    kirjed, page = [], 1
    while True:
        ls = post({"f": f, "ps": 50, "p": page})
        for e in ls["data"]:
            ev = e["event"]
            kirjed.append({
                "d": (ev.get("date") or "")[:10],
                "n": ev.get("title"),
                "algus": ev.get("startTime"),
                "v": (ev.get("venue") or {}).get("name"),
                "ala": ((ev.get("venue") or {}).get("area") or {}).get("name"),
                "b": [a["name"] for a in ev.get("artists") or []],
                "g": [g["name"] for g in ev.get("genres") or []],
                "url": "https://ra.co" + (ev.get("contentUrl") or ""),
                "pilet": bool(ev.get("isTicketed")),
            })
        if len(kirjed) >= ls["totalResults"] or not ls["data"]:
            break
        page += 1
        time.sleep(1)   # viisakas tempo
    VALJUND.write_text(json.dumps({
        "tommatud": date.today().isoformat(),
        "aken": {"algus": algus, "lopp": lopp},
        "allikas": "ra.co/graphql, area %d (All Estonia)" % AREA_ALL_ESTONIA,
        "nb": ("Toorandmed sweep-agendile: EI lahe automaatselt saidile. "
               "Skoop (peavoolu kommertsklubid VALJA), kahe allika reegel ja "
               "rikastamine jaavad kureerimise osaks."),
        "kirjeid": len(kirjed),
        "kirjed": kirjed,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"OK: {VALJUND} — {len(kirjed)} RA kirjet aknas {algus}..{lopp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
