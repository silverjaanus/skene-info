#!/usr/bin/env python3
"""rap.skene.info andmekorje: rap/data/manual.json (+ tulevased auto-allikad) -> rap/data/data.json

Serveripoolseid rapi-allikaid on vahe (Piletilevi/Fienta/Songkick JS voi blokitud);
pohisisend on nadalane Chrome-sweep, mis kirjutab manual.json-i.
Arhiiv (rap/data/archive/<aasta>.json) on akumuleeruv - vt scripts/archive_split.py.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAP = ROOT / "rap" / "data"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from archive_split import split_and_write
from common import (load_blocklist, load_manual, fail_if_manual_blocked,
                    warn_unknown_bands)


def main():
    manual = load_manual(RAP / "manual.json")
    block, block_names, block_artists = load_blocklist(RAP / "blocklist.json")
    # Blokitud kirje manual.json-is = viga, katkestab korje (vt common.py).
    fail_if_manual_blocked(manual, block, block_names, block_artists, sait="rap")
    n_cur, n_arch = split_and_write(RAP, manual, block=block, block_names=block_names,
                                    block_artists=block_artists)
    print(f"rap: data.json {n_cur}, arhiiv {n_arch}")
    try:
        warn_unknown_bands(RAP, manual)
    except Exception as ex:
        print(f"bands-kontroll vahele jaetud: {type(ex).__name__}: {ex}")
    try:
        import build_api
        n_ev, n_ar = build_api.build()
        print(f"api: events {n_ev}, archive {n_ar}")
    except Exception as ex:
        print(f"build_api vahele jaetud: {type(ex).__name__}: {ex}")


if __name__ == "__main__":
    main()
