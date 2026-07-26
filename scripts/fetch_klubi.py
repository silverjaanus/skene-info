#!/usr/bin/env python3
"""klubi.skene.info andmekorje: klubi/data/manual.json -> klubi/data/data.json

Pohisisend on nadalane Chrome-sweep + kontaktivorm (nagu rap-poolel).
Arhiiv (klubi/data/archive/<aasta>.json) on akumuleeruv - vt scripts/archive_split.py.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KLUBI = ROOT / "klubi" / "data"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from archive_split import split_and_write
from common import load_blocklist, is_blocked, warn_unknown_bands


def main():
    manual = json.loads((KLUBI / "manual.json").read_text(encoding="utf-8"))
    block, block_names = load_blocklist(KLUBI / "blocklist.json")
    manual = [e for e in manual if not is_blocked(e, block, block_names)]
    n_cur, n_arch = split_and_write(KLUBI, manual, block=block, block_names=block_names)
    print(f"klubi: data.json {n_cur}, arhiiv {n_arch}")
    try:
        warn_unknown_bands(KLUBI, manual)
    except Exception as ex:
        print(f"bands-kontroll vahele jaetud: {type(ex).__name__}: {ex}")
    try:
        from build_api import build as build_api_build
        n_ev, n_ar = build_api_build()
        print(f"api: events {n_ev}, archive {n_ar}")
    except Exception as ex:
        print(f"build_api vahele jaetud: {type(ex).__name__}: {ex}")


if __name__ == "__main__":
    main()
