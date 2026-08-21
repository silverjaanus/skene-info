#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""koristus_nadal.py -- nadal/ (ja soovi korral postitused/) retention.

Taust (21.08.2026 audit): nadal/ kasvas piiramatult (53 faili / ~10 MB kahe
kuuga, +5..9 jpg nadalas) ja SAMAD jpg-d dubleerusid postitused/-is (~18 MB).
Make.com loeb AINULT latest.json-i ja jooksva nadala pilte — vanadel failidel
pole ei saidil ega automaatikas tarbijat, nad ainult paisutavad repot/deployd.

MIDA: hoiab nadal/-is viimase N (vaikimisi 8) KUUPAEVAGRUPI failid
(nadal-YYYY-MM-DD*.jpg) + latest.json; vanemad kustutab. Jookseb iga paev
Andmekorjes (update.yml; kustutused commititakse). --postitused koristab ka
lokaalse postitused/ kausta (gitignore'itud): kuupaevaga failid (jpg/md/html)
vanemad kui N gruppi; send-log-*.txt jaavad alles.

Kasutus:
  python scripts/koristus_nadal.py                # nadal/, hoia 8 nadalat
  python scripts/koristus_nadal.py --hoia 12
  python scripts/koristus_nadal.py --postitused   # + postitused/ (lokaalne)
  python scripts/koristus_nadal.py --dry-run
"""
import argparse, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KP = re.compile(r"(\d{4}-\d{2}-\d{2})")


def korista_kaust(kaust, hoia, dry, muster="*"):
    if not kaust.exists():
        return 0
    grupid = {}
    for f in kaust.glob(muster):
        if f.name == "latest.json" or f.name.startswith("send-log"):
            continue
        m = KP.search(f.name)
        if not m:
            continue
        grupid.setdefault(m.group(1), []).append(f)
    kuupaevad = sorted(grupid)
    vanad = kuupaevad[:-hoia] if len(kuupaevad) > hoia else []
    n = 0
    for kp in vanad:
        for f in grupid[kp]:
            print(("KUSTUTAKS: " if dry else "kustutan: ") + str(f.relative_to(ROOT)))
            if not dry:
                f.unlink()
            n += 1
    print(f"{kaust.name}/: {len(kuupaevad)} kuupaevagruppi, hoian {min(hoia, len(kuupaevad))}, "
          f"{'kustutaks' if dry else 'kustutasin'} {n} faili")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hoia", type=int, default=8, help="mitu kuupaevagruppi alles (vaikimisi 8)")
    ap.add_argument("--postitused", action="store_true", help="korista ka postitused/ (lokaalne)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    korista_kaust(ROOT / "nadal", a.hoia, a.dry_run)
    if a.postitused:
        korista_kaust(ROOT / "postitused", a.hoia, a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
