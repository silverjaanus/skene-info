#!/usr/bin/env python3
"""rap.skene.info andmekorje: rap/data/manual.json (+ tulevased auto-allikad) -> rap/data/data.json

Serveripoolseid rapi-allikaid on vahe (Piletilevi/Fienta/Songkick JS voi blokitud);
pohisisend on nadalane Chrome-sweep, mis kirjutab manual.json-i.
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAP = ROOT / "rap" / "data"

def main():
    manual = json.loads((RAP / "manual.json").read_text(encoding="utf-8"))
    blockfile = RAP / "blocklist.json"
    if blockfile.exists():
        import re, unicodedata
        def slug(s):
            s = unicodedata.normalize("NFKD", s.lower())
            return re.sub(r"[^a-z0-9]+", "", s)
        block = {(b["d"], slug(b["n"])) for b in json.loads(blockfile.read_text(encoding="utf-8"))}
        manual = [e for e in manual if (e["d"], slug(e["n"])) not in block]
    manual.sort(key=lambda e: e["d"])
    out = {"updated": date.today().isoformat(), "entries": manual}
    (RAP / "data.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"rap: {len(manual)} kirjet")

if __name__ == "__main__":
    main()
