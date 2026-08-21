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
from common import (load_blocklist, load_manual, fail_if_manual_blocked,
                    warn_unknown_bands)


def main():
    manual = load_manual(KLUBI / "manual.json")
    block, block_names, block_artists = load_blocklist(KLUBI / "blocklist.json")
    # Blokitud kirje manual.json-is = viga, katkestab korje (vt common.py).
    fail_if_manual_blocked(manual, block, block_names, block_artists, sait="klubi")
    n_cur, n_arch = split_and_write(KLUBI, manual, block=block, block_names=block_names,
                                    block_artists=block_artists)
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
