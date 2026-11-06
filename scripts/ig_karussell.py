#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ig_karussell.py -- postitab nadala karusselli (nadal/latest.json) otse Instagrami API-ga.

06.11.2026: Make'i Facebooki uhendus tuhistati (Meta kontode uhendamine 05.11) ja
karussell jai postitamata. See skript kasutab sama oma Meta appi tokenit (IG_TOKEN)
mis story'd (scripts/ig_publish.py), seega Make'ist ei soltu.

Kaitsed:
  - latest.json["date"] peab olema selle nadala reede (vaikimisi: tana) -- vana pilti ei postita;
  - kui @skene.info-l on TANA juba CAROUSEL_ALBUM, ei postita uuesti (topeltpostituse kaitse);
  - --dry-run ainult kontrollib.

Kasutus:  IG_TOKEN=... python scripts/ig_karussell.py [--dry-run] [--force-date]
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, urllib.error
import datetime as dt
from zoneinfo import ZoneInfo

GRAPH = "https://graph.instagram.com/v23.0"
IG_USER_ID = "17841409504581888"     # @skene.info
TZ = ZoneInfo("Europe/Tallinn")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def call(method, path, params):
    data = urllib.parse.urlencode(params)
    if method == "GET":
        req = urllib.request.Request(f"{GRAPH}/{path}?{data}")
    else:
        req = urllib.request.Request(f"{GRAPH}/{path}", data=data.encode(), method="POST")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=90).read())
    except urllib.error.HTTPError as e:
        sys.exit(f"VIGA {e.code} {path.split('?')[0]}: {e.read().decode('utf-8', 'replace')[:500]}")


def oota_valmis(cid, token):
    for _ in range(40):
        s = call("GET", cid, {"fields": "status_code", "access_token": token}).get("status_code")
        if s == "FINISHED":
            return
        if s == "ERROR":
            sys.exit(f"VIGA: Instagram ei suutnud konteinerit {cid} tootelda")
        time.sleep(3)
    sys.exit(f"VIGA: konteiner {cid} ei saanud valmis 2 minutiga")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    token = os.environ.get("IG_TOKEN", "").strip()
    if not token:
        sys.exit("VIGA: IG_TOKEN puudub")

    lj = json.load(open(os.path.join(REPO, "nadal", "latest.json"), encoding="utf-8"))
    tana = dt.datetime.now(TZ).date()
    if lj.get("date") != tana.isoformat():
        sys.exit(f"VIGA: latest.json on {lj.get('date')}, mitte {tana} -- vana pilti ei postita")
    urls = lj.get("image_urls") or [lj["image_url"]]
    urls = urls[:10]                         # IG karusselli piir
    cap = lj.get("caption", "")
    if len(cap) > 2200:
        sys.exit(f"VIGA: caption {len(cap)} marki > 2200")

    m = call("GET", "me/media", {"fields": "media_type,timestamp,permalink", "limit": 10, "access_token": token})
    for x in m.get("data", []):
        t = dt.datetime.strptime(x["timestamp"], "%Y-%m-%dT%H:%M:%S%z").astimezone(TZ)
        if t.date() == tana and x.get("media_type") == "CAROUSEL_ALBUM":
            print(f"Tanane karussell on juba olemas: {x.get('permalink')} -- ei postita uuesti")
            return
    for u in urls:
        r = urllib.request.urlopen(urllib.request.Request(u + "?v=" + str(int(time.time())), method="HEAD"), timeout=30)
        if r.status != 200:
            sys.exit(f"VIGA: {u} -> {r.status}")
    print(f"{len(urls)} pilti, caption {len(cap)} marki")
    if a.dry_run:
        print("DRY-RUN: ei postita"); return

    lapsed = []
    for u in urls:
        c = call("POST", f"{IG_USER_ID}/media", {"image_url": u, "is_carousel_item": "true", "access_token": token})
        lapsed.append(c["id"])
    for cid in lapsed:
        oota_valmis(cid, token)
    k = call("POST", f"{IG_USER_ID}/media", {"media_type": "CAROUSEL", "children": ",".join(lapsed),
                                              "caption": cap, "access_token": token})
    oota_valmis(k["id"], token)
    p = call("POST", f"{IG_USER_ID}/media_publish", {"creation_id": k["id"], "access_token": token})
    info = call("GET", p["id"], {"fields": "permalink,timestamp", "access_token": token})
    print(f"POSTITATUD: {info.get('permalink')} ({info.get('timestamp')})")


if __name__ == "__main__":
    main()
