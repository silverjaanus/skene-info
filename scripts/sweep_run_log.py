#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sweep_run_log.py -- sweep-jooksu arvepidamine failina (21.08.2026 audit).

MIKS: sweep-prompt nouab labikaigu arvet ("allikaid kokku X, avatud Y,
skipitud Z") ainult jooksu KOKKUVOTTES -- parast jooksu pole KUSKIL failina
kontrollitav, mitu allikat tegelikult avati. Kui FB-seanss katkeb keset
sweepi ja pool allikaid jaab labimata, on koik valved rohelised
(check_sweep_varskus naeb ainult taielikku 8-paevast vaikust).

MIDA: sweep-agent jooksutab selle SKRIPTI vahetult enne commit-sammu; skript
valideerib arvud (avatud + skipitud == allikaid) ja kirjutab
sweep/run-YYYY-MM-DD.json. Sweepi commit (git add sweep/) viib faili repo'sse.
check_sweep_varskus.py valvab CI-s, et varskeim run-fail poleks piirist vanem
(ISEARMEERUV: valve hakkab kehtima alles esimese run-faili ilmumisest).

Kasutus (sweep, enne commit-sammu):
  python scripts/sweep_run_log.py --allikaid 153 --avatud 150 ^
      --uusi-www 6 --uusi-rap 0 --uusi-klubi 7 ^
      --skip "https://fb.com/x|leht kustutatud" --skip "https://y.ee|timeout" ^
      --markus "FB seanss katkes korra, jatkasin"
Vaatamine:  python scripts/sweep_run_log.py --naita
"""
import argparse, json, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KAUST = ROOT / "sweep"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allikaid", type=int, help="allikaid sources.json-is kokku")
    ap.add_argument("--avatud", type=int, help="mitu allikat paris avati")
    ap.add_argument("--uusi-www", type=int, default=0)
    ap.add_argument("--uusi-rap", type=int, default=0)
    ap.add_argument("--uusi-klubi", type=int, default=0)
    ap.add_argument("--skip", action="append", default=[],
                    help='vahelejaanud allikas kujul "url|pohjus" (korduv)')
    ap.add_argument("--markus", default="")
    ap.add_argument("--kuupaev", default=None, help="YYYY-MM-DD (vaikimisi tana)")
    ap.add_argument("--naita", action="store_true", help="naita varskeimat run-faili")
    a = ap.parse_args()

    if a.naita:
        failid = sorted(KAUST.glob("run-*.json"))
        if not failid:
            print("Yhtegi sweep/run-*.json faili pole veel.")
            return 0
        print(failid[-1].name)
        print(failid[-1].read_text(encoding="utf-8"))
        return 0

    if a.allikaid is None or a.avatud is None:
        ap.error("--allikaid ja --avatud on kohustuslikud (voi kasuta --naita)")

    skipitud = []
    for s in a.skip:
        url, _, pohjus = s.partition("|")
        skipitud.append({"url": url.strip(), "pohjus": pohjus.strip() or "pohjus puudub!"})

    # arvepidamine peab klappima: iga allikas on kas avatud voi pohjusega skipitud
    if a.avatud + len(skipitud) != a.allikaid:
        print(f"VIGA: avatud ({a.avatud}) + skipitud ({len(skipitud)}) != allikaid "
              f"({a.allikaid}). Iga vahelejaetud allikas vajab --skip \"url|pohjus\" "
              f"kirjet — vaikimisi (pohjendamata) vahelejatt ON viga (sweep-prompti "
              f"KATVUSE REEGEL).")
        return 1

    kp = a.kuupaev or date.today().isoformat()
    fail = KAUST / f"run-{kp}.json"
    fail.write_text(json.dumps({
        "kuupaev": kp,
        "allikaid": a.allikaid,
        "avatud": a.avatud,
        "skipitud": skipitud,
        "uusi": {"www": a.uusi_www, "rap": a.uusi_rap, "klubi": a.uusi_klubi},
        "markus": a.markus,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"OK: {fail} kirjutatud ({a.avatud}/{a.allikaid} avatud, "
          f"{len(skipitud)} skipitud, uusi www {a.uusi_www} / rap {a.uusi_rap} / "
          f"klubi {a.uusi_klubi}). Commit viib selle repo'sse (git add sweep/).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
