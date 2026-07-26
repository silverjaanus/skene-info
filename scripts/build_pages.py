# -*- coding: utf-8 -*-
"""Genereerib kolme saidi index.html failid uhest template'ist.

  python scripts/build_pages.py           # kirjutab failid
  python scripts/build_pages.py --check   # ainult vordleb, ei kirjuta

Allikas: templates/base.html (uhine osa, pesad {{Snnn}}) + templates/site-<sait>.json
(pesade vaartused; pikad vaartused viitavad failile templates/snippets/<sait>/Snnn.html).

TAHTIS: muudatused tehakse TEMPLATE'i / konfi, MITTE index.html failidesse otse.
Kui --check utleb ERINEB, on keegi index.html-i kasitsi muutnud - kanna see muudatus
enne ulegenereerimist template'i, muidu see kaob. Vt templates/README.md.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"
OUT = {"www": ROOT / "index.html",
       "rap": ROOT / "rap" / "index.html",
       "klubi": ROOT / "klubi" / "index.html"}


def rd(path):
    """Loeb faili reavahetusi muutmata (baithaaval-identsus on siin kriitiline)."""
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def render(sait):
    """Asendab base.html pesad selle saidi vaartustega ja tagastab valmis HTML-i."""
    base = rd(TPL / "base.html")
    with open(TPL / ("site-%s.json" % sait), encoding="utf-8") as f:
        cfg = json.load(f)
    for sid, val in cfg.items():
        if isinstance(val, dict):          # {"f": "snippets/www/S007.html"}
            val = rd(TPL / val["f"])
        base = base.replace("{{%s}}\n" % sid, val)
    if "{{S" in base:
        jaak = [r for r in base.splitlines() if r.strip().startswith("{{S")]
        sys.exit("VIGA (%s): taitmata pesa(d): %s" % (sait, ", ".join(jaak[:5])))
    return base


def esimene_erinevus(a, b):
    """Tagastab inimloetava viite esimesele erinevusele (rida ja veerg)."""
    ar, br = a.splitlines(), b.splitlines()
    for i in range(min(len(ar), len(br))):
        if ar[i] != br[i]:
            veerg = next((j for j in range(min(len(ar[i]), len(br[i])))
                          if ar[i][j] != br[i][j]), min(len(ar[i]), len(br[i])))
            return "rida %d, veerg %d" % (i + 1, veerg + 1)
    if len(ar) != len(br):
        return "ridade arv erineb (%d vs %d)" % (len(ar), len(br))
    return "ainult reavahetused/lopumark"


def main():
    check = "--check" in sys.argv
    vigu = 0
    for sait, path in OUT.items():
        uus = render(sait)
        vana = rd(path) if path.exists() else None
        h_uus = hashlib.sha256(uus.encode("utf-8")).hexdigest()[:12]
        h_vana = hashlib.sha256(vana.encode("utf-8")).hexdigest()[:12] if vana is not None else "-"
        sama = (uus == vana)
        if check:
            if sama:
                print("OK      %-5s %s (%s)" % (sait, path.name, h_uus))
            else:
                vigu += 1
                print("ERINEB  %-5s %s: template %s vs fail %s -> %s"
                      % (sait, path.name, h_uus, h_vana, esimene_erinevus(uus, vana or "")))
        elif sama:
            print("muutmata %-5s %s" % (sait, path.name))
        else:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(uus)
            print("kirjutatud %-5s %s (%s)" % (sait, path.name, h_uus))
    if check and vigu:
        print("\n%d fail(i) erineb. Kanna kasitsi tehtud muudatus template'i ENNE ulegenereerimist." % vigu)
        sys.exit(1)


if __name__ == "__main__":
    main()
