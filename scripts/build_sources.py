#!/usr/bin/env python3
"""skene.info allikate leht: sweep/sources.json -> avalik data/allikad.json (+ rap).

Puhastab sisemised nb-margmed valja; jatab ainult jalgitavad lehed (nimi + url).
Jookseb fetch.py lopus (guarditud), nii et iga korje voi manuaalne allika lisamine
hoiab avaliku allikate lehe varskena. Genereeritud, kasitsi ei muudeta.
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "sweep" / "sources.json"

# allika tyyp -> avaliku grupi nimi (eestikeelne; leht tolgib pealkirjad EN-i JS-is)
GROUP = {
    "promootor": "Korraldajad",
    "venue": "Kohad",
    "venue/DIY": "Kohad",
    "festival": "Festivalid",
    "label": "Plaadifirmad ja poed",
    "pood": "Plaadifirmad ja poed",
    "pood/kultuuripunkt": "Plaadifirmad ja poed",
    "kogukond": "Kogukond",
    "artist": "Artistid",
}
ORDER_MAIN = ["Korraldajad", "Kohad", "Festivalid", "Plaadifirmad ja poed",
              "Kogukond", "Instagram", "Rahvusvahelised festivalid", "Muud"]
ORDER_RAP = ["Festivalid", "Kohad", "Korraldajad", "Instagram / artistid", "Muud"]


def _ok(url):
    return isinstance(url, str) and url.startswith("http")


def _add(groups, gname, nimi, url):
    if not _ok(url) or not nimi:
        return
    items = groups.setdefault(gname, [])
    if any(i["u"] == url for i in items):
        return
    items.append({"n": nimi.strip(), "u": url.strip()})


def _pack(groups, order):
    out = []
    for g in order:
        items = sorted(groups.get(g, []), key=lambda i: i["n"].lower())
        if items:
            out.append({"nimi": g, "items": items})
    for g, items in groups.items():  # order-vabad grupid lopetuseks
        if g not in order and items:
            out.append({"nimi": g, "items": sorted(items, key=lambda i: i["n"].lower())})
    return out


def build():
    data = json.loads(SRC.read_text(encoding="utf-8"))

    main = {}
    for e in data.get("fb", []):
        _add(main, GROUP.get(e.get("tyyp", ""), "Muud"), e.get("nimi", ""), e.get("url", ""))
    for e in data.get("ig", []):
        _add(main, "Instagram", e.get("nimi", ""), e.get("url", ""))
    for e in data.get("rock_punk_uued", {}).get("sites", []):
        _add(main, GROUP.get(e.get("tyyp", ""), "Muud"), e.get("nimi", ""), e.get("url", ""))
    intl = data.get("rahvusvaheline", {})
    for region in ("baltikum", "pohjamaad", "euroopa"):
        for e in intl.get(region, []):
            nimi = e.get("nimi", "")
            if e.get("riik"):
                nimi = f"{nimi} ({e['riik']})"
            _add(main, "Rahvusvahelised festivalid", nimi, e.get("url", ""))

    rap = {}
    rd = data.get("rap", {})
    for e in rd.get("fb", []):
        _add(rap, GROUP.get(e.get("tyyp", ""), "Muud"), e.get("nimi", ""), e.get("url", ""))
    for e in rd.get("ig", []):
        _add(rap, "Instagram / artistid", e.get("nimi", ""), e.get("url", ""))

    today = date.today().isoformat()
    g_main, g_rap = _pack(main, ORDER_MAIN), _pack(rap, ORDER_RAP)
    (ROOT / "data" / "allikad.json").write_text(
        json.dumps({"updated": today, "groups": g_main}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (ROOT / "rap" / "data" / "allikad.json").write_text(
        json.dumps({"updated": today, "groups": g_rap}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return sum(len(g["items"]) for g in g_main), sum(len(g["items"]) for g in g_rap)


if __name__ == "__main__":
    nm, nr = build()
    print(f"allikad: peasait {nm}, rap {nr}")
