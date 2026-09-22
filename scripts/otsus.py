#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""otsus.py -- lahtiste otsustuspunktide haldus (sweep/otsused.json).

Taust (22.09.2026): punkti sulgemine tahendas seni KASITSI kahe faili
muutmist -- otsused.json-ist kustutamine + HANDOVER 4 proosa umberkirjutamine
+ suletud kirje ARCHIVE'i tostmine. 22.09 tegin seda neli korda uhes jooksus.
Nuud on see uks kask.

Kasutus:
  python scripts/otsus.py --loend
  python scripts/otsus.py --lisa uus.json
  python scripts/otsus.py --sulge <oid> --vastus a --markus "Silver: jaab valja"
  python scripts/otsus.py --sulge <oid> --vaikeotsus --markus "5 p vastuseta"

--sulge teeb korraga:
  1. votab punkti otsused.json-ist valja,
  2. kirjutab suletud kirje verbatim HANDOVER-ARCHIVE.md loppu (koos linkidega,
     REEGLID 8 -- ka valjajaetul peab link alles jaama),
  3. renderdab HANDOVER 4 ploki uuesti (render_handover.py).

NB: HANDOVER.md ja HANDOVER-ARCHIVE.md on PRIVAATSES repos -- commit `priv.bat`-iga.
    sweep/otsused.json on AVALIKUS repos (dash loeb seda) -- tavaline `git add`.
"""
import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OTSUSED = ROOT / "sweep" / "otsused.json"
ARCHIVE = ROOT / "HANDOVER-ARCHIVE.md"

NOUTUD = ("oid", "kysimus", "valikud", "vaikeotsus", "tahtaeg")


def laadi():
    if not OTSUSED.exists():
        return []
    d = json.loads(OTSUSED.read_text(encoding="utf-8"))
    return d if isinstance(d, list) else []


def salvesta(d):
    OTSUSED.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def renderda():
    import render_handover
    render_handover.main()


def valideeri(o):
    puudu = [k for k in NOUTUD if not o.get(k)]
    if puudu:
        raise SystemExit("VIGA: punktil puuduvad valjad: %s" % ", ".join(puudu))
    if not o.get("lingid"):
        print("HOIATUS: punktil '%s' ei ole uhtegi linki. REEGLID 8 nouab kontroll-linke "
              "VOI selget marget, mida otsiti ja kust." % o["oid"])
    ids = [v.get("id") for v in o.get("valikud") or []]
    if o.get("vaikeotsus") not in ids:
        raise SystemExit("VIGA: vaikeotsus '%s' ei ole valikute seas %s" % (o.get("vaikeotsus"), ids))


def cmd_loend():
    d = laadi()
    if not d:
        print("Lahtisi punkte ei ole.")
        return
    for o in sorted(d, key=lambda x: str(x.get("tahtaeg"))):
        print("%-46s | tahtaeg %s | vaikeotsus %s | %s"
              % (o.get("oid"), o.get("tahtaeg"), o.get("vaikeotsus"),
                 (o.get("kysimus") or "")[:60]))


def cmd_lisa(fail):
    uus = json.loads(Path(fail).read_text(encoding="utf-8"))
    uued = uus if isinstance(uus, list) else [uus]
    d = laadi()
    olemas = {o.get("oid") for o in d}
    for o in uued:
        valideeri(o)
        if o["oid"] in olemas:
            print("vahele (oid juba olemas): %s" % o["oid"])
            continue
        o.setdefault("lisatud", date.today().isoformat())
        d.append(o)
        print("lisatud: %s" % o["oid"])
    salvesta(d)
    renderda()


def cmd_sulge(oid, vastus, markus, vaikeotsus):
    d = laadi()
    punkt = next((o for o in d if o.get("oid") == oid), None)
    if punkt is None:
        raise SystemExit("VIGA: oid '%s' ei ole otsused.json-is. Vt --loend." % oid)

    if vaikeotsus:
        vastus = punkt.get("vaikeotsus")
        alus = "VAIKEOTSUS (5 p vastuseta, TOOVOOG 1 reegel 16c) -- tagasipooratav"
    else:
        if not vastus:
            raise SystemExit("VIGA: anna --vastus <id> voi --vaikeotsus")
        alus = "SILVERI VASTUS"

    ids = [v.get("id") for v in punkt.get("valikud") or []]
    if vastus not in ids:
        raise SystemExit("VIGA: vastus '%s' ei ole valikute seas %s" % (vastus, ids))
    valitud = next(v for v in punkt["valikud"] if v["id"] == vastus)

    read = [
        "",
        "## Suletud otsustuspunkt %s -- %s" % (date.today().isoformat(), oid),
        "",
        "**Kusimus:** %s" % punkt.get("kysimus"),
        "",
        "**Otsus: (%s) %s**" % (vastus, valitud.get("tekst")),
        "",
        "Alus: %s%s" % (alus, (" -- " + markus) if markus else ""),
        "",
        "Vaikeotsus oli: (%s) | tahtaeg oli %s | punkt lisatud %s"
        % (punkt.get("vaikeotsus"), punkt.get("tahtaeg"), punkt.get("lisatud", "?")),
        "",
        "Koik valikud, mis laual olid:",
    ]
    for v in punkt.get("valikud") or []:
        read.append("- (%s) %s" % (v.get("id"), v.get("tekst")))
    read.append("")
    read.append("Kontroll-lingid (REEGLID 8 -- ka valjajaetul peab link alles jaama):")
    for l in (punkt.get("lingid") or []) or ["*(linke ei olnud)*"]:
        read.append("- %s" % l)
    if punkt.get("kontekst"):
        read += ["", "Kontekst punkti esitamise hetkel:", "", str(punkt["kontekst"])]
    read.append("")

    with ARCHIVE.open("a", encoding="utf-8") as f:
        f.write("\n".join(read) + "\n")

    salvesta([o for o in d if o.get("oid") != oid])
    print("suletud: %s -> (%s) %s" % (oid, vastus, valitud.get("tekst")[:60]))
    print("ARCHIVE'i kirjutatud, otsused.json-ist eemaldatud.")
    renderda()
    print("NB: HANDOVER.md + HANDOVER-ARCHIVE.md -> `priv.bat`; otsused.json -> tavaline git.")


def main():
    p = argparse.ArgumentParser(description="Lahtiste otsustuspunktide haldus.")
    p.add_argument("--loend", action="store_true")
    p.add_argument("--lisa", metavar="FAIL.json")
    p.add_argument("--sulge", metavar="OID")
    p.add_argument("--vastus", metavar="ID")
    p.add_argument("--vaikeotsus", action="store_true")
    p.add_argument("--markus", default="")
    a = p.parse_args()

    if a.lisa:
        cmd_lisa(a.lisa)
    elif a.sulge:
        cmd_sulge(a.sulge, a.vastus, a.markus, a.vaikeotsus)
    else:
        cmd_loend()


if __name__ == "__main__":
    main()
