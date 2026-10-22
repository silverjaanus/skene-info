#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ig_karussell_kontroll.py -- kas reedene karussell (Make 6485652) on paris Instagramis (22.10.2026).

Make postitab karusselli R 11:45, aga repos sellest jalge ei jaa. See skript kusib
Instagrami API-lt @skene.info viimased postitused (storyd sinna ei kuulu) ja kirjutab
valvur/ig.json: viimase postituse aeg + kas tana on postitus olemas.
Jookseb uudiskirja workflow lopus; valvur (R 12:15) loeb faili.
Vajab IG_TOKEN keskkonnamuutujat. Exit 1, kui tanast postitust pole.
"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request
from zoneinfo import ZoneInfo

GRAPH = "https://graph.instagram.com/v23.0"
try:
    TZ = ZoneInfo("Europe/Tallinn")
except Exception:   # Windowsi Pythonil pole tzdata -- seal on kohalik aeg niikuinii Eesti aeg
    TZ = None
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "valvur", "ig.json")


def _nyyd():
    return dt.datetime.now(TZ) if TZ else dt.datetime.now().astimezone()


def main():
    token = os.environ.get("IG_TOKEN", "").strip()
    tana = _nyyd().date()
    d = {"kontrollitud": _nyyd().isoformat(timespec="minutes")}
    if not token:
        d.update(seis="viga", pohjus="IG_TOKEN puudub")
    else:
        q = urllib.parse.urlencode({"fields": "id,media_type,timestamp,permalink",
                                    "limit": 5, "access_token": token})
        try:
            r = json.loads(urllib.request.urlopen(f"{GRAPH}/me/media?{q}", timeout=60).read())
            m = r.get("data", [])
            viimane = m[0] if m else {}
            ts = viimane.get("timestamp")
            kohalik = dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").astimezone(TZ) if ts else None
            d.update(viimane_aeg=kohalik.isoformat(timespec="minutes") if kohalik else None,
                     viimane_tyyp=viimane.get("media_type"), viimane_link=viimane.get("permalink"),
                     seis="ok" if kohalik and kohalik.date() == tana else "tanast_postitust_pole")
        except Exception as e:
            d.update(seis="viga", pohjus=f"{type(e).__name__}: {str(e)[:200]}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(d, ensure_ascii=False))
    sys.exit(0 if d["seis"] == "ok" else 1)


if __name__ == "__main__":
    main()
