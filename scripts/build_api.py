#!/usr/bin/env python3
"""Avalik API: koondab koigi kolme saidi (www/rap/klubi) kirjed
staatilisteks JSON-failideks, mida Vercel serveerib.

  api/events.json  - tulevased + featured kirjed (saitide data.json sisu),
                     igal kirjel lisavali "sait" (www|rap|klubi)
  api/archive.json - kogu arhiiv (moodunud kirjed) aastate kaupa kokku,
                     sama "sait" vali

Kutsutakse fetch.py / fetch_rap.py / fetch_klubi.py lopus (guarditud
try/except) - iga andmekorje ja sweep uuendab API automaatselt.
CORS: Access-Control-Allow-Origin:* on feed-/api-JSONidel olemas —
Vercel lisab selle staatikale vaikimisi JA alates 13.08.2026 on see ka
vercel.json routes-headers plokis eksplitsiitselt (per-route 'headers'
+ 'continue' TOOTAB legacy routes sees; varasem vaide, et ei saa, oli
vale — kaib top-level 'headers' sektsiooni kohta). Brauserist saab
feedi lugeda otse.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_entries, today_local
# NB: peakataloogi failid elavad kaustas feed/, MITTE api/ -- niipea kui juurkausta
# api/ sisse tekkis Verceli funktsioon (api/eelistused.js), peitis Vercel kogu selle
# kausta staatilisest valjundist ja /api/events.json andis 404. Avalikud URLid on
# endised: vercel.json routes suunab /api/events.json -> /feed/events.json.
# Alamsaitide (rap/, klubi/) api-kaustad on puutumata -- piirang kehtib ainult juurkaustale.
API = ROOT / "feed"

SITES = [
    ("www", ROOT / "data"),
    ("rap", ROOT / "rap" / "data"),
    ("klubi", ROOT / "klubi" / "data"),
]

# Pisipildi "img" on saidi enda failides SUHTELINE ("pildid/x.webp"), sest iga
# sait serveerib oma kausta. Koondfeedis see kuju ei toimi: www lehel lahenduks
# klubi kirje pilt vastu /pildid/ (= metal-kaust) ja annaks 404. Juurest algav
# tee ("/klubi/pildid/x.webp") EI kolba ka, sest vercel.json host-route teeb
# klubi.skene.info-l /(.*) -> /klubi/$1 ehk tekiks /klubi/klubi/pildid/...
# Ainus kuju, mis toimib koigil kolmel hostil, on taielik URL.
IMG_HOST = {
    "www": "https://www.skene.info",
    "rap": "https://rap.skene.info",
    "klubi": "https://klubi.skene.info",
}

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
    "img": "pisipildi taielik URL (https://<sait>.skene.info/pildid/...); puudub, kui pilti pole",
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


def _write(path, sisu, entries):
    out = {
        "updated": today_local().isoformat(),
        "_meta": _meta(sisu),
        "count": len(entries),
        "entries": entries,
    }
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                    encoding="utf-8")


def _pub(sait, e):
    """Kirje avalikuks: lisab 'sait' ja teeb 'img' taielikuks URLiks."""
    out = {"sait": sait, **e}
    img = out.get("img")
    if isinstance(img, str) and img and not img.startswith(("http://", "https://")):
        out["img"] = f"{IMG_HOST[sait]}/{img.lstrip('/')}"
    return out


def build():
    """Tagastab (n_events, n_archive)."""
    API.mkdir(exist_ok=True)
    events, archive = [], []
    for sait, ddir in SITES:
        for e in load_entries(ddir / "data.json"):
            events.append(_pub(sait, e))
        adir = ddir / "archive"
        if adir.exists():
            for f in sorted(adir.glob("[0-9][0-9][0-9][0-9].json")):
                for e in load_entries(f):
                    archive.append(_pub(sait, e))
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
