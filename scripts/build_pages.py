# -*- coding: utf-8 -*-
"""Genereerib saitide HTML-lehed uhest template'ist (index, arhiiv, allikad x www/rap/klubi).

  python scripts/build_pages.py            # kirjutab failid
  python scripts/build_pages.py --check    # ainult vordleb, ei kirjuta (valjumiskood 1 kui erineb)
  python scripts/build_pages.py index      # ainult uks lehepere

Allikas: templates/<leht>/base.html (uhine osa, pesad {{Snnn}}) + site-<sait>.json
(pesade vaartused; pikad viitavad failile snippets/<sait>/Snnn.html).

TAHTIS: muudatused tehakse TEMPLATE'i, MITTE genereeritud HTML-i. Kui --check utleb ERINEB,
on keegi HTML-i kasitsi muutnud - kanna muudatus enne ulegenereerimist template'i.
Vt templates/README.md.

REAVAHETUSED: template hoiab alati LF-i. Valjund kirjutatakse selles konventsioonis, mis
sihtfailis juba on (repos on CRLF ja LF segamini + core.autocrlf=true muudab neid kloonimisel).
Nii ei anna --check valehairet teises kloonis ega teisel platvormil.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"
SAIDID = ("www", "rap", "klubi")
LEHED = {
    "index":   {"www": "index.html",   "rap": "rap/index.html",   "klubi": "klubi/index.html"},
    "arhiiv":  {"www": "arhiiv.html",  "rap": "rap/arhiiv.html",  "klubi": "klubi/arhiiv.html"},
    "allikad": {"www": "allikad.html", "rap": "rap/allikad.html", "klubi": "klubi/allikad.html"},
}


def rd_lf(path):
    """Loeb faili ja normaliseerib reavahetused LF-iks."""
    with open(path, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def rd_raw(path):
    """Loeb faili baithaaval samamoodi nagu ta kettal on (vordluseks)."""
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def faili_reavahetus(path):
    """Milline reavahetus sihtfailis juba on. Uue faili puhul LF."""
    if not path.exists():
        return "\n"
    b = path.read_bytes()
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n") - crlf
    return "\r\n" if crlf > lf else "\n"


def render(leht, sait, eol="\n"):
    """Asendab base.html pesad selle saidi vaartustega."""
    d = TPL / leht
    out = rd_lf(d / "base.html")
    with open(d / ("site-%s.json" % sait), encoding="utf-8") as f:
        cfg = json.load(f)
    for sid, val in cfg.items():
        if isinstance(val, dict):                      # {"f": "snippets/www/S007.html"}
            val = rd_lf(d / val["f"])
        out = out.replace("{{%s}}\n" % sid, val.replace("\r\n", "\n"))
    if "{{S" in out:
        jaak = [r.strip() for r in out.splitlines() if r.strip().startswith("{{S")]
        sys.exit("VIGA (%s/%s): taitmata pesa(d): %s" % (leht, sait, ", ".join(jaak[:5])))
    return out.replace("\n", eol) if eol != "\n" else out


# --- varuandmestik (E_FALLBACK) -------------------------------------------------
# Leht naitab seda ainult siis, kui data.json ei laadi. Sisu vananeb, seetottu saab
# selle siit uuesti genereerida: python scripts/build_pages.py --fallback
FALLBACK_PESA = "S060"                 # templates/index/snippets/<sait>/S060.html
FALLBACK_MAX = 40
VALJA_JARJEKORD = ["d", "d2", "t", "n", "a", "b", "v", "linn", "c", "g", "img",
                   "sn", "su", "on_", "ou", "pu", "yu", "hind", "hind2",
                   "rel", "lisatud", "tba", "nb"]


def js_kirje(e):
    """Uks kirje JS-objekti literaalina (votmed ilma jutumarkideta, nagu senises failis)."""
    osad = []
    for k in VALJA_JARJEKORD:
        if k in e and e[k] not in (None, "", [], {}):
            osad.append("%s:%s" % (k, json.dumps(e[k], ensure_ascii=False)))
    return " {%s}" % ",".join(osad)


def uuenda_fallback():
    """Kirjutab iga saidi varuandmestiku uuesti selle saidi data/data.json pealt."""
    from datetime import date
    tana = date.today().isoformat()
    for leht_sait, suhtetee in (("www", "data/data.json"),
                                ("rap", "rap/data/data.json"),
                                ("klubi", "klubi/data/data.json")):
        andmed = json.loads(rd_lf(ROOT / suhtetee))
        kirjed = andmed["entries"] if isinstance(andmed, dict) else andmed
        tulevased = sorted([e for e in kirjed if e.get("d", "") >= tana],
                           key=lambda e: e.get("d", ""))[:FALLBACK_MAX]
        sisu = ",\n".join(js_kirje(e) for e in tulevased) + "\n"
        siht = TPL / "index" / "snippets" / leht_sait / ("%s.html" % FALLBACK_PESA)
        with open(siht, "w", encoding="utf-8", newline="") as f:
            f.write(sisu)
        print("varuandmestik %-5s %d kirjet -> %s" % (leht_sait, len(tulevased), siht.name))


def esimene_erinevus(a, b):
    """Inimloetav viide esimesele erinevusele."""
    ar, br = a.splitlines(), b.splitlines()
    for i in range(min(len(ar), len(br))):
        if ar[i] != br[i]:
            n = min(len(ar[i]), len(br[i]))
            veerg = next((j for j in range(n) if ar[i][j] != br[i][j]), n)
            return "rida %d, veerg %d" % (i + 1, veerg + 1)
    if len(ar) != len(br):
        return "ridade arv erineb (%d vs %d)" % (len(ar), len(br))
    return "ainult reavahetused/lopumark"


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("-")]
    check = "--check" in sys.argv
    if "--fallback" in sys.argv:
        uuenda_fallback()
        if check:
            sys.exit("--fallback ja --check koos ei ole moistlikud (fallback muudab template'i).")
    lehed = argv or list(LEHED)
    tundmatu = [l for l in lehed if l not in LEHED]
    if tundmatu:
        sys.exit("Tundmatu leht: %s (valikud: %s)" % (", ".join(tundmatu), ", ".join(LEHED)))
    vigu = 0
    for leht in lehed:
        for sait in SAIDID:
            path = ROOT / LEHED[leht][sait]
            uus = render(leht, sait, faili_reavahetus(path))
            vana = rd_raw(path) if path.exists() else None
            h = hashlib.sha256(uus.encode("utf-8")).hexdigest()[:12]
            silt = "%s/%s" % (leht, sait)
            if uus == vana:
                print(("OK      " if check else "muutmata ") + "%-14s %s" % (silt, h))
            elif check:
                vigu += 1
                print("ERINEB  %-14s %s -> %s" % (silt, h, esimene_erinevus(uus, vana or "")))
            else:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(uus)
                print("kirjutatud %-11s %s" % (silt, h))
    if check and vigu:
        print("\n%d fail(i) erineb. Kanna kasitsi tehtud muudatus template'i ENNE ulegenereerimist." % vigu)
        sys.exit(1)


if __name__ == "__main__":
    main()
