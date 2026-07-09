#!/usr/bin/env python3
"""rap.skene.info andmekorje: rap/data/manual.json (+ tulevased auto-allikad) -> rap/data/data.json

Serveripoolseid rapi-allikaid on vahe (Piletilevi/Fienta/Songkick JS voi blokitud);
pohisisend on nadalane Chrome-sweep, mis kirjutab manual.json-i.
Arhiiv (rap/data/archive/<aasta>.json) on akumuleeruv - vt scripts/archive_split.py.
"""
import json, re, sys, unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAP = ROOT / "rap" / "data"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from archive_split import split_and_write


def slug(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9]+", "", s)


def main():
    manual = json.loads((RAP / "manual.json").read_text(encoding="utf-8"))
    blockfile = RAP / "blocklist.json"
    block, block_names = set(), set()
    if blockfile.exists():
        raw = json.loads(blockfile.read_text(encoding="utf-8"))
        block = {(b["d"], slug(b["n"])) for b in raw if "d" in b}
        block_names = {slug(b["n"]) for b in raw if "d" not in b}
        manual = [e for e in manual
                  if (e["d"], slug(e["n"])) not in block and slug(e["n"]) not in block_names]
    n_cur, n_arch = split_and_write(RAP, manual, block=block, block_names=block_names)
    print(f"rap: data.json {n_cur}, arhiiv {n_arch}")
    try:
        from fetch import warn_unknown_bands
        warn_unknown_bands(RAP, manual)
    except Exception as ex:
        print(f"bands-kontroll vahele jaetud: {type(ex).__name__}: {ex}")


if __name__ == "__main__":
    main()
