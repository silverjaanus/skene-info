# -*- coding: utf-8 -*-
"""
fetch_prices.py — korjab piletihinnad Fienta lehtedelt ja kirjutab `hind` valja.

MIKS SEE OLEMAS ON
  `hind` oli varem AINULT kasitsi taidetav vali: uks korje ei puutunud seda, nii
  et hind ilmus kirjesse ainult siis, kui keegi sweepi ajal piletilehe lahti tegi.
  13.09.2026 seisuga oli 102-st tulevasest uritusest hind olemas 27-l ja 42-l oli
  piletilink ilma hinnata. Neist 26 oli Fienta.

  ⚠ Vanemates kirjetes on `nb`-vali "Piletihinda EI onnestunud Fienta lehelt
  tekstina katte saada (hinnad on ostuvoos)". SEE ON VALE JARELDUS. Hinnad EI ole
  ainult ostuvoos: Fienta lehe HTML sisaldab schema.org `Offer`-plokke
  ({"price": "15.00", "priceCurrency": "EUR", "availability": ...}). Tavaline
  €-regex neid ei leia, sest lehel pole eurosummasid tekstina. Otsi `"price"`.

MIDA SEE KIRJUTAB
  hind = {"praegu": "13–15 €", "allikas": "Fienta (automaatne), kontrollitud PP.KK.AAAA"}
  Silveri otsus 13.09.2026: LIHTNE VAHEMIK, ei mingeid astmeid ega margikusi.
  Kes tahab osta, laheb niikuinii piletilehele ja naeb, mis saadaval on.
  Kui lehel on teenustasu, saab vahemik saba "+ tasu" (Fiental ei ole, Piletitaskul on).

MIDA SEE EI TEE
  - EI kirjuta ule kasitsi sisestatud hinda. Kasitsi hind voib olla LAIEM kui
    piletimuuja oma (nt uksehind FB-postitusest, mida Fienta ei tea):
    "Evestus 20€/25€" vs Fienta 20 € — kasitsi on oigem, see jaab alles.
  - EI puuduta moodunud kirjeid.
  - EI kirjuta hinda, kui koik hinnaastmed on labi muudud (parem tuhi kui vale).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (compatible; skene.info hinnakorje; +https://skene.info)"}
VIIVITUS = 1.0          # sekundit paringute vahel — ara koorma piletimuujat
AEGUMINE = 30

SAIDID = {
    "www": ROOT / "data" / "manual.json",
    "rap": ROOT / "rap" / "data" / "manual.json",
    "klubi": ROOT / "klubi" / "data" / "manual.json",
}

# Astmed, mis EI ole tavaline sissepaas. Need jaavad vahemikust VALJA, sest muidu
# tuleb rampsu: saatjapilet 0 € tegi Kaschalotist "0–20 €" ja Chelsea Wolfe'i
# VIP-pakett tegi temast "30–293,95 €" (moodetud 13.09.2026 testis).
TOETUS = re.compile(r"toetaj|supporter|sponsor|package|experience|realization|"
                    r"annetu|donat|\bvip\b", re.I)
# ⚠ SOODUSPILETID ON VAHEMIKUS SEES (Silveri otsus 13.09.2026): õpilane, pensionär,
# noor, erivajadusega külastaja. Kaschalot = 15–20 €, mitte 20 €. Saatjapilet (0 €)
# jääb ikka välja, aga seda teeb juba `p > 0` filter, mitte nimemuster.

TASU_SONAD = ("teenustasu", "service fee", "broneerimistasu", "booking fee", "tehingutasu")

MARKER = "(automaatne)"   # hind.allikas sisaldab seda -> selle kirje tohib ule kirjutada


def lae(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=AEGUMINE) as r:
        return r.read().decode("utf-8", "replace")


def pakkumised(html: str) -> list[dict]:
    """Koik schema.org Offer-kirjed lehelt."""
    out = []
    for blk in re.findall(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", html, re.S):
        try:
            data = json.loads(blk.strip())
        except Exception:
            continue
        stack = [data]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                if "price" in cur and ("priceCurrency" in cur or cur.get("@type") == "Offer"):
                    try:
                        hind = float(cur["price"])
                    except (TypeError, ValueError):
                        hind = None
                    out.append({
                        "nimi": (cur.get("name") or "").strip(),
                        "p": hind,
                        "valuuta": (cur.get("priceCurrency") or "EUR").strip(),
                        "saadaval": "SoldOut" not in str(cur.get("availability") or ""),
                    })
                stack.extend(cur.values())
            elif isinstance(cur, list):
                stack.extend(cur)
    return out


def summa(x: float) -> str:
    """15.0 -> '15'; 15.9 -> '15,90'; eesti kirjapilt, koma on kumnendkoht."""
    return (f"{x:.2f}".rstrip("0").rstrip(".")).replace(".", ",")


def vahemik(pakk: list[dict], tasu: bool) -> tuple[str | None, str]:
    """-> (hinnastring voi None, pohjendus logi jaoks)"""
    kehtiv = [x for x in pakk if x["p"] is not None and x["p"] > 0]
    if not kehtiv:
        return None, "hinnaastmeid ei leitud (voi koik 0 €)"
    saadaval = [x for x in kehtiv if x["saadaval"]]
    if not saadaval:
        return None, "koik astmed labi muudud — hinda ei kirjutata"
    pohi = [x for x in saadaval if not TOETUS.search(x["nimi"])]
    if not pohi:
        pohi = saadaval          # ainult toetajapiletid -> parem miski kui mitte midagi
    val = {x["valuuta"] for x in pohi}
    yhik = "€" if val <= {"EUR"} else next(iter(val))
    n = sorted({x["p"] for x in pohi})
    tekst = f"{summa(n[0])} {yhik}" if len(n) == 1 else f"{summa(n[0])}–{summa(n[-1])} {yhik}"
    if tasu:
        tekst += " + tasu"
    pohjendus = f"{len(pakk)} astet -> {len(pohi)} arvesse"
    if len(n) > 1 and n[-1] / n[0] > 4:
        pohjendus += "  ⚠ LAI VAHEMIK, vaata ule"
    return tekst, pohjendus


def tana() -> str:
    return dt.date.today().strftime("%d.%m.%Y")


def ule_kirjutatav(e: dict, refresh: bool) -> bool:
    h = e.get("hind")
    if not h:
        return True
    return bool(refresh and MARKER in (h.get("allikas") or ""))


def tootle_sait(nimi: str, tee: Path, args) -> tuple[int, int]:
    if not tee.exists():
        print(f"[{nimi}] {tee} puudub, jatan vahele")
        return 0, 0
    kirjed = json.loads(tee.read_text(encoding="utf-8"))
    piir = dt.date.today().isoformat()
    kandidaadid = [
        e for e in kirjed
        if "fienta.com" in (e.get("pu") or "")
        and (e.get("d") or "9999") >= piir
        and ule_kirjutatav(e, args.refresh)
    ]
    print(f"\n=== {nimi}: {len(kandidaadid)} kandidaati ({tee.name}) ===")
    muudetud = 0
    vigu = 0
    for e in kandidaadid:
        nimetus = (e.get("n") or "?")[:46]
        try:
            html = lae(e["pu"])
        except urllib.error.HTTPError as ex:
            print(f"  !! {nimetus} — HTTP {ex.code} ({e['pu']})")
            vigu += 1
            time.sleep(VIIVITUS)
            continue
        except Exception as ex:
            print(f"  !! {nimetus} — {ex}")
            vigu += 1
            time.sleep(VIIVITUS)
            continue
        tasu = any(s in html.lower() for s in TASU_SONAD)
        tekst, pohjendus = vahemik(pakkumised(html), tasu)
        if not tekst:
            print(f"  -- {nimetus} — {pohjendus}")
        else:
            print(f"  OK {nimetus} — {tekst}   ({pohjendus})")
            if not args.dry_run:
                e["hind"] = {"praegu": tekst,
                             "allikas": f"Fienta {MARKER}, kontrollitud {tana()}"}
            muudetud += 1
        time.sleep(VIIVITUS)
    if muudetud and not args.dry_run:
        # ⚠ ILMA loputa reavahetuseta — manual.json on repos ilma selleta,
        # muidu tekib iga jooksuga mottetu uherealine diff.
        tee.write_text(json.dumps(kirjed, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print(f"[{nimi}] kirjutatud {muudetud} hinda -> {tee.name}")
    return muudetud, vigu


def main():
    ap = argparse.ArgumentParser(description="Korjab piletihinnad Fientalt manual.json-i.")
    ap.add_argument("--dry-run", action="store_true",
                    help="naita, mis kirjutataks, aga ARA kirjuta")
    ap.add_argument("--refresh", action="store_true",
                    help="varskenda ka juba automaatselt taidetud hindu (kasitsi omad jaavad puutumata)")
    ap.add_argument("--sait", choices=sorted(SAIDID), action="append",
                    help="ainult see sait (vaikimisi koik)")
    args = ap.parse_args()

    saidid = args.sait or list(SAIDID)
    kokku = vigu = 0
    for s in saidid:
        m, v = tootle_sait(s, SAIDID[s], args)
        kokku += m
        vigu += v

    print(f"\nKOKKU: {kokku} hinda" + (" (DRY RUN — midagi ei kirjutatud)" if args.dry_run else ""))
    if vigu:
        print(f"VIGU: {vigu} — katkine piletilink voi leht kadunud, vaata ule")
    if kokku and not args.dry_run:
        print("JARGMISENA: python scripts/fetch.py  (+ klubi/rap korjed, kui neid muudeti)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
