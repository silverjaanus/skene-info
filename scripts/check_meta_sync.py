#!/usr/bin/env python3
"""Kontrollib, et fetch.py GENRE_META ja genereeritud index.html/arhiiv.html
JS-koopiad (templates/ snippetitest) on omavahel synkis (13.08.2026 audit:
tabel on kasitsi mitmes kohas, syncit hoidis seni ainult kommentaar).

Jooksuta:  python scripts/check_meta_sync.py   (voi check_dupes.py kaudu)
Valjumiskood 1, kui midagi erineb. Paranda templates/ ja jooksuta build_pages.py.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch import GENRE_META as PY_META  # noqa: E402


def parse_js(path):
    txt = Path(path).read_text(encoding="utf-8")
    m = re.search(r"const GENRE_META=\{(.*?)\};", txt, re.S)
    if not m:
        return None, None
    pairs = re.findall(r'(?:"([^"]+)"|([A-Za-z0-9_-]+)):\[([^\]]*)\]', m.group(1))
    d = {}
    for qk, k, vals in pairs:
        d[qk or k] = [v.strip().strip('"') for v in vals.split(",") if v.strip()]
    mm = re.search(r"const METAS=\[([^\]]*)\]", txt)
    metas = [v.strip().strip('"') for v in mm.group(1).split(",")] if mm else None
    return d, metas


def main():
    vigu = 0
    py = {k: list(v) for k, v in PY_META.items()}
    vals = {m for v in py.values() for m in v}
    for f in ("index.html", "arhiiv.html"):
        js, metas = parse_js(ROOT / f)
        if js is None:
            print(f"META-SYNC {f}: GENRE_META plokki ei leidnud")
            vigu += 1
            continue
        if js != py:
            only_py = sorted(set(py) - set(js))
            only_js = sorted(set(js) - set(py))
            diff = sorted(k for k in set(py) & set(js) if py[k] != js[k])
            print(f"META-SYNC {f} ERINEB fetch.py-st: puudu {only_py}, "
                  f"ule {only_js}, erinev {diff}")
            vigu += 1
        if metas and not vals <= set(metas):
            print(f"META-SYNC {f}: METAS-ist puudub {sorted(vals - set(metas))}")
            vigu += 1
    if vigu:
        print(f"META-SYNC: {vigu} viga — muuda templates/ snippeteid ja jooksuta "
              "python scripts/build_pages.py")
        return 1
    print("META-SYNC: fetch.py / index.html / arhiiv.html GENRE_META synkis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
