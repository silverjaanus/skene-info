#!/usr/bin/env python3
"""Puhastab manual.json-idest MOODUNUD kirjed, mis on ARHIIVIS kinnitatult
olemas (Silveri otsus 13.08.2026: manual ei jaa kogu-too failiks, arhiiv on
toe allikas moodunu kohta).

Kirje eemaldatakse manual.json-ist AINULT siis, kui KOIK kolm tingimust kehtivad:
  1. loppkuupaev (common.end_date) on rohkem kui PUHVER paeva minevikus;
  2. kirje EI ole enam data.json-is (st pole current/featured — nt varske
     reliis pusib 30 paeva featured'ina ja jaab puutumata);
  3. TAPSELT sama voti (d + slug(n), sama loogika mis archive_split._key)
     on arhiivifailis olemas — ilma arhiivikinnituseta ei kustutata midagi.

Blocklisti pole vaja: kirje on juba moodunud ja arhiivis; archive_split ei
too seda LIVE-poolele tagasi (arhiiv on akumuleeruv, data.json = tulevased).

Jookseb paevases workflow's parast fetch-samme (update.yml); kaib ka kasitsi:
    python scripts/prune_manual.py [--dry-run]
"""
import json
import sys
from pathlib import Path
from datetime import timedelta

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import end_date, today_local, load_entries  # noqa: E402
from archive_split import _key  # noqa: E402

PUHVER_PAEVI = 14

SAIDID = {
    "www": ROOT / "data",
    "rap": ROOT / "rap" / "data",
    "klubi": ROOT / "klubi" / "data",
}


def main(dry_run=False):
    piir = (today_local() - timedelta(days=PUHVER_PAEVI)).isoformat()
    kokku = 0
    for sait, kaust in SAIDID.items():
        mp = kaust / "manual.json"
        if not mp.exists():
            continue
        manual = json.loads(mp.read_text(encoding="utf-8"))
        live = {_key(e) for e in load_entries(kaust / "data.json")}
        arhiiv = set()
        for f in sorted((kaust / "archive").glob("[0-9][0-9][0-9][0-9].json")):
            arhiiv |= {_key(e) for e in load_entries(f)}

        jaab, valja = [], []
        for e in manual:
            k = _key(e)
            ed = end_date(e)
            if ed and ed < piir and k not in live and k in arhiiv:
                valja.append(e)
            else:
                jaab.append(e)

        if valja:
            kokku += len(valja)
            print(f"prune {sait}: -{len(valja)} (manual {len(manual)} -> {len(jaab)}); "
                  f"piir {piir}, koik arhiivis kinnitatud")
            for e in valja:
                print(f"  - {e.get('d')} {e.get('n')}")
            if not dry_run:
                mp.write_text(json.dumps(jaab, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8")
        else:
            print(f"prune {sait}: pole midagi eemaldada")
    if dry_run and kokku:
        print(f"DRY-RUN: kokku {kokku} kirjet eemaldataks, midagi ei kirjutatud")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
