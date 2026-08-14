#!/usr/bin/env python3
"""Valve: kirja SAATMISTEE ja eelvaate tee ei tohi lahku minna.

MIKS SEE FAIL OLEMAS ON (14.08.2026):
  13.08 parandati kuupaevaloogika (kaimasolev tuur naitab jargmist toimumis-
  kuupaeva) ja 14.08 lisati kategooriate labisegi jarjestus. Molemad laksid
  make_weekly_email.gen_combo()-sse. Aga send_weekly.py -- AINUS tee, mis jouab
  paris tellijani -- ei kutsu gen_combo()-t: sel oli oma koopia sortimisest.
  Tulemus: eelvaade oli oige, 14.08 valjalainud kiri naitas 02.08 ja 05.08
  kuupaevi ning koiki metal-kirjeid eesotsas.

Kontrollib kaht asja:
  A) STRUKTUUR -- uheski generaatoris ega saatmisskriptis ei tohi olla OMA
     jarjestusloogikat; jarjestus tuleb ainult common.order_for_output()-ist.
  B) KAITUMINE -- paris andmetega genereeritud nimekiri rahuldab invariante:
     kuupaevad kasvavad, ukski kirje ei naita akna algusest varasemat kuupaeva,
     ja sama paeva kategooriad on labisegi.

Kasutus:  python scripts/check_send_parity.py [--repo .] [--date YYYY-MM-DD]
Valjub koodiga 1, kui midagi on katki (sobib CI-sse).
"""
import argparse
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CAT_ORDER, this_and_next_week, order_for_output, parse_d
import make_weekly_email as gen

HERE = os.path.dirname(os.path.abspath(__file__))

# Failid, mis EI TOHI ise jarjestada. Muster otsib kirje-loendi sortimist ja
# _disp kasitsi maaramist -- tapselt need read, mis 14.08 lahku laksid.
VALVATUD = ["send_weekly.py", "make_weekly_email.py", "make_weekly_image.py",
            "make_weekly_caption.py"]
KEELATUD = [
    (re.compile(r'\.sort\(\s*key\s*=\s*lambda\s+e\s*:'), "oma sort(key=lambda e: ...)"),
    (re.compile(r'\[\s*["\']_disp["\']\s*\]\s*='), "oma _disp maaramine"),
    (re.compile(r'\binterleave_cats\s*\('), "interleave_cats() otsekutse"),
]


def kontrolli_struktuur():
    vead = []
    for nimi in VALVATUD:
        path = os.path.join(HERE, nimi)
        if not os.path.exists(path):
            vead.append(f"{nimi}: faili pole (kas nimi muutus?)")
            continue
        src = open(path, encoding="utf-8").read()
        # kommentaarid valja, et selgitav tekst ei annaks valehairet
        kood = "\n".join(r.split("#")[0] for r in src.splitlines())
        for muster, selgitus in KEELATUD:
            if muster.search(kood):
                vead.append(f"{nimi}: {selgitus} -- jarjestus peab tulema "
                            f"common.order_for_output()-ist")
        if "order_for_output(" not in kood:
            vead.append(f"{nimi}: ei kutsu order_for_output() -- kas jarjestus jai vahele?")
    return vead


def kontrolli_kaitumine(repo, ref):
    vead = []
    ws, we = this_and_next_week(ref)
    all_ev = gen.load_sources(repo, ws, we)
    if not all_ev:
        # Tyhi aken ei ole KOODI viga (voib olla vaikne nadal) -- hoiatus, mitte kukkumine.
        print(f"  HOIATUS: aknas {ws}..{we} pole uhtegi kirjet, kaitumiskontroll jai tegemata.")
        return []

    # Kombinatsioonid, mida saatmine tegelikult kasutab.
    kombod = [["metal"], ["metal", "rap"], ["metal", "rap", "klubi"],
              ["rap", "klubi"], ["klubi"]]
    for cats in kombod:
        sel = [dict(e) for e in all_ev if e.get("_cat") in cats]
        if not sel:
            continue
        sel = order_for_output(sel, ws)
        tag = "+".join(cats)

        # 1) ukski kuvatav kuupaev ei tohi olla akna algusest varasem
        for e in sel:
            disp = e.get("_disp") or e.get("d", "")
            if disp < ws.isoformat():
                vead.append(f"[{tag}] '{e.get('n','?')}' kuvab {disp}, "
                            f"aken algab {ws} (moodunud alguskuupaev!)")

        # 2) kuvatavad kuupaevad peavad kasvama
        kuup = [(e.get("_disp") or e.get("d", "")) for e in sel]
        if kuup != sorted(kuup):
            vead.append(f"[{tag}] kuupaevad ei ole kasvavas jarjekorras")

        # 3) sama paeva sees peavad kategooriad olema labisegi: round-robini
        #    korral sisaldavad paeva esimesed k kirjet (k = eri kategooriaid)
        #    iga kategooriat tapselt uks kord
        i = 0
        while i < len(sel):
            _k = lambda e: e.get("_disp") or e.get("d", "")
            j = i
            while j < len(sel) and _k(sel[j]) == _k(sel[i]):
                j += 1
            grp = sel[i:j]
            eri = {e.get("_cat") for e in grp}
            if len(eri) > 1:
                esimesed = [e.get("_cat") for e in grp[:len(eri)]]
                if set(esimesed) != eri:
                    vead.append(f"[{tag}] {_k(grp[0])}: kategooriad ei ole labisegi "
                                f"(algus: {esimesed}, paevas on {sorted(eri)})")
            i = j
    return vead


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.dirname(HERE))
    ap.add_argument("--date", default=None)
    a = ap.parse_args()
    ref = parse_d(a.date) if a.date else dt.date.today()

    sv = kontrolli_struktuur()
    print("STRUKTUURIVIGA:" if sv else
          "OK struktuur: koik neli skripti kutsuvad order_for_output()-i, "
          "oma jarjestusloogikat pole.")
    kv = kontrolli_kaitumine(a.repo, ref)
    print("KAITUMISVIGA:" if kv else
          "OK kaitumine: kuupaevad kasvavad, moodunud alguskuupaevi pole, "
          "kategooriad labisegi.")

    koik = sv + kv
    for v in koik:
        print("  - " + v)
    if koik:
        print(f"\nKOKKU {len(koik)} viga. Kiri EI OLE saatmiskolblik.")
        return 1
    print("\nKirja jarjestus on korras.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
