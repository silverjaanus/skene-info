#!/usr/bin/env python3
"""Avalik API: koondab koigi kolme saidi (www/rap/klubi) kirjed
staatilisteks JSON-failideks, mida Vercel serveerib.

  api/events.json  - tulevased + featured kirjed (saitide data.json sisu),
                     igal kirjel lisavali "sait" (www|rap|klubi)
  api/archive.json - kogu arhiiv (moodunud kirjed) aastate kaupa kokku,
                     sama "sait" vali

Kutsutakse fetch.py / fetch_rap.py / fetch_klubi.py lopus (guarditud
try/except) - iga andmekorje ja sweep uuendab API automaatselt.
CORS-pais puudub teadlikult (vercel.json legacy 'routes' ei luba
'headers' sektsiooni) - serveripoolne GET seda ei vaja; kui tekib
brauseripohine tarbija, tuleb routes -> rewrites+headers migreerida.
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = ROOT / "api"

SITES = [
    ("www", ROOT / "data"),
    ("rap", ROOT / "rap" / "data"),
    ("klubi", ROOT / "klubi" / "data"),
]

FIELDS = {
    "sait": "alamdomeen: www (metal/rock/punk, www.skene.info) | rap (Eesti hip-hop, rap.skene.info) | klubi (elektrooniline klubikultuur, klubi.skene.info)",
    "d": "alguskuupaev ISO (AAAA-KK-PP); reliisil valjalaskekuupaev",
    "d2": "loppkuupaev 'PP.KK' (ainult mitmepaevastel)",
    "t": "tyyp: kontsert | festival | klubi | reliis | merch",
    "n": "nimi",
    "a": "kirjeldus (ET)",
    "b": "esinejad/bandid (list)",
    "v": "toimumiskoht (venue)",
    "c": "linnakategooria: Tallinn | Tartu | mujal | valisriikide puhul riik/regioon",
    "linn": "tapsem linn (kui c=mujal)",
    "g": "zanrisildid (list)",
    "sn": "avastusallika nimi",
    "su": "avastusallika URL",
    "on_": "urituse ametliku allika nimi",
    "ou": "urituse ametlik URL (nt FB event)",
    "pu": "piletimyygi URL",
    "yu": "urituse/sarja YouTube URL",
    "hind": "hinnaobjekt: praegu, mark, kuni, jargmine, allikas",
    "rel": "1 = reliisi/merchi kirje (naidatakse 'uus' 30 paeva alates 'lisatud')",
    "lisatud": "saidile lisamise kuupaev (reliisidel, 'uus' 30 paeva)",
    "tba": "1 = koosseis/detailid alles tapsustamisel",
    "nb": "vabatekstiline markus",
}


def _meta(sisu):
    return {
        "info": f"skene.info avalik API - {sisu}. Eesti alternatiivmuusika: "
                "kontserdid, festivalid, klubiohtud, reliisid, merch.",
        "kasutus": "Tasuta. Palume viidata allikale (skene.info) ja sailitada "
                   "kirjete allikaviited (ou/su/pu). Kirjete andmed ET keeles.",
        "uueneb": "iga paev ~07:30 EET (andmekorje) + nadalane sweep (P oosel)",
        "urls": {
            "events": "https://www.skene.info/api/events.json",
            "archive": "https://www.skene.info/api/archive.json",
        },
        "kontakt": "kontaktivorm www.skene.info sidebaris",
        "fields": FIELDS,
    }


def _entries(path):
    if not path.exists():
        return []
    try:
        j = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(j, dict):
        return j.get("entries", [])
    return j if isinstance(j, list) else []


def _write(path, sisu, entries):
    out = {
        "updated": date.today().isoformat(),
        "_meta": _meta(sisu),
        "count": len(entries),
        "entries": entries,
    }
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                    encoding="utf-8")


def build():
    """Tagastab (n_events, n_archive)."""
    API.mkdir(exist_ok=True)
    events, archive = [], []
    for sait, ddir in SITES:
        for e in _entries(ddir / "data.json"):
            events.append({"sait": sait, **e})
        adir = ddir / "archive"
        if adir.exists():
            for f in sorted(adir.glob("[0-9][0-9][0-9][0-9].json")):
                for e in _entries(f):
                    archive.append({"sait": sait, **e})
    events.sort(key=lambda e: (e.get("d", ""), e.get("n", "")))
    archive.sort(key=lambda e: (e.get("d", ""), e.get("n", "")))
    _write(API / "events.json", "tulevased + varsked kirjed", events)
    _write(API / "archive.json", "arhiiv (moodunud kirjed)", archive)

    # Koond-events.json koopiad alamdomeenidele. Vercel routes suunab
    # rap.skene.info/api/* -> /rap/api/*, seega saidi enda otsing (index.html)
    # laeb "api/events.json" relatiivselt oma kaustast. Sama sisu koigil kolmel.
    for sub in ("rap", "klubi"):
        subapi = ROOT / sub / "api"
        subapi.mkdir(parents=True, exist_ok=True)
        _write(subapi / "events.json", "tulevased + varsked kirjed", events)

    return len(events), len(archive)


if __name__ == "__main__":
    n_ev, n_ar = build()
    print(f"api: events.json {n_ev}, archive.json {n_ar}")
