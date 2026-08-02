#!/usr/bin/env python3
"""Otsib KAHTLASI DUPLIKAATE koigi kolme saidi andmetest.

Miks see olemas on (02.08.2026): saidile oli tekkinud mitu duplikaati, mida ukski
olemasolev kontroll ei puudnud:
  1. sama uritus kahest AUTO-allikast veidi eri nimega (HAINZ / Hainz ... TASUTA)
  2. manual.json-i lisatud kirje, mis oli juba olemas (Fuzzolini reliis)
  3. kirje 'd' muudeti -> archive_split sailitas ka vana kuupaevaga koopia (Kosmikud)
  4. manual.json-ist kustutatud kirje tuli eelmisest data.json-ist tagasi (Molbo, KRS-One)

Jooksuta PARAST fetch-skripte:
    python scripts/check_dupes.py
Valjundis on ainult KAHTLUSED - inimene otsustab. Valjumiskood 1, kui midagi leiti.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import slug  # noqa: E402

SAIDID = {
    "www": ROOT / "data",
    "rap": ROOT / "rap" / "data",
    "klubi": ROOT / "klubi" / "data",
}


def load(p):
    if not p.exists():
        return []
    raw = json.loads(p.read_text(encoding="utf-8"))
    return raw.get("entries", raw) if isinstance(raw, dict) else raw


def bandset(e):
    return {slug(b) for b in e.get("b", []) if b}


def nimeleid(a, b):
    """Kas uks nimi sisaldub teises (slugi tasandil) - lyhikesed valistatud."""
    if len(a) < 8 or len(b) < 8:
        return False
    return a in b or b in a


def kirjeldus(e):
    osad = [e.get("d", "?")]
    if e.get("d2"):
        osad.append("-" + e["d2"])
    osad.append(e.get("n", "?"))
    if e.get("v"):
        osad.append("@ " + e["v"])
    if e.get("sn"):
        osad.append("[" + e["sn"] + "]")
    return " ".join(osad)


def leia_dupid(kirjed):
    """Kahtlus = SAMA kuupaev JA (nimeleid VOI bandi-kattuvus VOI sama venue)."""
    hits = []
    for i in range(len(kirjed)):
        for j in range(i + 1, len(kirjed)):
            a, b = kirjed[i], kirjed[j]
            if a.get("d") != b.get("d"):
                continue
            na, nb = slug(a.get("n", "")), slug(b.get("n", ""))
            if na == nb:
                hits.append(("SAMA NIMI", a, b))
                continue
            ba, bb = bandset(a), bandset(b)
            va, vb = slug(a.get("v", "") or ""), slug(b.get("v", "") or "")
            reliisid = a.get("t") == "reliis" and b.get("t") == "reliis"
            if nimeleid(na, nb):
                hits.append(("nimi sisaldub", a, b))
            elif ba and bb and (ba & bb):
                hits.append(("sama band: " + ", ".join(sorted(ba & bb)), a, b))
            elif va and va == vb and not reliisid:
                # NB: kaks reliisi samal paeval jagavad 'v' valja ("Bandcamp") -
                # see EI ole duplikaat, seega reliiside puhul kohareeglit ei rakenda
                hits.append(("sama koht", a, b))
    return hits


def leia_kadunud(sait, kaust):
    """manual.json-ist puuduvad, aga data.json-is olevad KURATEERITUD kirjed.
    Need on tavaliselt eelmisest data.json-ist sailinud kummitused (vt archive_split)."""
    manual = load(kaust / "manual.json")
    data = load(kaust / "data.json")
    man_keys = {(e.get("d"), slug(e.get("n", ""))) for e in manual}
    auto_sn = {"Metal Storm", "The Krypt FB", "thekrypt.ee", "paavli.ee", "helitehas.ee"}
    kummitused = []
    for e in data:
        k = (e.get("d"), slug(e.get("n", "")))
        if k in man_keys:
            continue
        if e.get("sn") in auto_sn:
            continue  # tuleb auto-allikast, normaalne
        kummitused.append(e)
    return kummitused


def main():
    vigu = 0
    for sait, kaust in SAIDID.items():
        data = load(kaust / "data.json")
        print(f"\n=== {sait} ({len(data)} kirjet data.json-is) ===")

        hits = leia_dupid(data)
        if hits:
            vigu += len(hits)
            print(f"  KAHTLASI DUPLIKAATE: {len(hits)}")
            for pohjus, a, b in hits:
                print(f"   - [{pohjus}]")
                print(f"       A: {kirjeldus(a)}")
                print(f"       B: {kirjeldus(b)}")
        else:
            print("  duplikaate ei leitud")

        kumm = leia_kadunud(sait, kaust)
        if kumm:
            vigu += len(kumm)
            print(f"  KUMMITUSI (data.json-is, aga mitte manual.json-is ega tuntud auto-allikast): {len(kumm)}")
            for e in kumm:
                print(f"   - {kirjeldus(e)}")

    if vigu:
        print(f"\nKOKKU {vigu} kahtlust. Kummituse kustutamiseks lisa blocklist.json-i "
              "kirje vana 'd' + 'n'-ga ja jooksuta fetch uuesti.")
        return 1
    print("\nKoik puhas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
