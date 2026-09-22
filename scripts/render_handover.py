#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_handover.py -- kirjutab HANDOVER.md 4 lahtiste punktide ploki
sweep/otsused.json pohjal.

Taust (22.09.2026): iga otsustuspunkt oli seni KAKS korda kasitsi kirjas --
proosana HANDOVER 4-s ja JSON-ina sweep/otsused.json-is (dash loeb sealt).
Sama duplikaat, mis tekitas 08.2026 REEGLID.md auditi (samad reeglid 3-4
koopias, kaks pairs vastuolu). Nuud on otsused.json AINUS toeallikas ja
see skript renderdab HANDOVER-i ploki.

Skript puutub AINULT markerite vahelist teksti:
    <!-- OTSUSED:ALGUS -->  ...  <!-- OTSUSED:LOPP -->
Koik muu HANDOVER-is jaab puutumata.

Vorm jargib REEGLID 8: kusimus + valikud (a/b) KOIGE EES, siis nimi/kuupaev/
koht ja KOIK kontroll-lingid, siis taust.

Kasutus:
  python scripts/render_handover.py            # kirjutab ploki
  python scripts/render_handover.py --dry-run  # naitab, ei kirjuta
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OTSUSED = ROOT / "sweep" / "otsused.json"
HANDOVER = ROOT / "HANDOVER.md"

ALGUS = "<!-- OTSUSED:ALGUS -->"
LOPP = "<!-- OTSUSED:LOPP -->"

HOIATUS = ("*Plokk on GENEREERITUD `sweep/otsused.json`-ist "
           "(`python scripts/render_handover.py`). ARA muuda kasitsi -- "
           "muuda JSON-i ja renderda uuesti.*")


def laadi():
    if not OTSUSED.exists():
        return []
    d = json.loads(OTSUSED.read_text(encoding="utf-8"))
    return d if isinstance(d, list) else []


def _paevi(tahtaeg):
    """Mitu paeva tahtajani; None kui kuupaev on katki."""
    try:
        y, m, d = (int(x) for x in str(tahtaeg).split("-"))
        return (date(y, m, d) - date.today()).days
    except Exception:
        return None


def vormista(punktid):
    if not punktid:
        return ("**LAHTISI PUNKTE EI OLE.** `sweep/otsused.json` on tuhi.\n\n"
                + HOIATUS + "\n")

    punktid = sorted(punktid, key=lambda o: (str(o.get("tahtaeg") or ""), o.get("oid") or ""))
    read = []
    for i, o in enumerate(punktid, 1):
        uus = "[UUS] " if str(o.get("lisatud") or "") == date.today().isoformat() else ""
        read.append("**%d. %s%s**" % (i, uus, o.get("kysimus") or "(kusimus puudub)"))

        vaike = o.get("vaikeotsus")
        for v in (o.get("valikud") or []):
            mark = " *(VAIKEOTSUS)*" if v.get("id") == vaike else ""
            read.append("**(%s)** %s%s" % (v.get("id"), v.get("tekst"), mark))

        t = o.get("tahtaeg")
        p = _paevi(t)
        kiire = ""
        if p is not None:
            if p < 0:
                kiire = " -- **TAHTAEG MOODAS, vaikeotsus rakendub SELLES jooksus**"
            elif p == 0:
                kiire = " -- **rakendub TANA**"
            elif p == 1:
                kiire = " -- rakendub HOMME"
        read.append("**Vaikeotsus rakendub %s**%s" % (t, kiire))
        read.append("")

        lingid = o.get("lingid") or []
        if lingid:
            read.append("Kontroll-lingid:")
            for l in lingid:
                read.append("- %s" % l)
        else:
            read.append("- *(otselinki ei ole -- REEGLID 8 jargi tuleb see valja kirjutada, "
                        "mida otsiti ja kust)*")
        read.append("")

        if o.get("kontekst"):
            read.append(str(o["kontekst"]))
            read.append("")
        read.append("`oid: %s`" % o.get("oid"))
        read.append("")
        if i < len(punktid):
            read.append("---")
            read.append("")

    n = len(punktid)
    pais = "**1 lahtine punkt.**" if n == 1 else "**%d lahtist punkti.**" % n
    return (pais + " Vasta meilile (nt „1a, 2b\") voi dashis.\n\n"
            + "\n".join(read) + "\n" + HOIATUS + "\n")


def kirjuta(tekst, dry=False):
    h = HANDOVER.read_text(encoding="utf-8")
    if ALGUS not in h or LOPP not in h:
        raise SystemExit(
            "VIGA: HANDOVER.md-s puuduvad markerid %s / %s. Lisa need 4 alla." % (ALGUS, LOPP))
    a = h.index(ALGUS) + len(ALGUS)
    b = h.index(LOPP)
    uus = h[:a] + "\n\n" + tekst.rstrip() + "\n\n" + h[b:]
    if dry:
        print(tekst)
        return False
    if uus == h:
        print("render_handover: muutusi ei ole")
        return False
    HANDOVER.write_text(uus, encoding="utf-8")
    return True


def main():
    dry = "--dry-run" in sys.argv
    punktid = laadi()
    muutus = kirjuta(vormista(punktid), dry=dry)
    if not dry:
        print("render_handover: %d lahtist punkti%s"
              % (len(punktid), " (HANDOVER uuendatud)" if muutus else ""))


if __name__ == "__main__":
    main()
