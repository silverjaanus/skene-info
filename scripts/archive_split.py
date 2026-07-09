#!/usr/bin/env python3
"""Jagab kirjed kaheks: data.json (tulevased + featured) ja arhiiv
(data/archive/<aasta>.json, aastate kaupa).

Arhiiv on AKUMULEERUV: olemasolevaid arhiivikirjeid ega eelmise data.json-i
sisu ei kaotata, isegi kui algallikas (Metal Storm, Fienta jne) enam möödunud
üritust ei tagasta. Nii jääb kõik, mis kunagi saidil oli, arhiivi alles.

Kasutavad nii scripts/fetch.py kui scripts/fetch_rap.py.
"""
import json, re, unicodedata
from datetime import date
from pathlib import Path

TODAY = date.today().isoformat()


def _slug(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9]+", "", s)


def _key(e):
    return (e.get("d", ""), _slug(e.get("n", "")))


def _featured(e):
    """Reliis/merch on 'uus' 30 päeva alates 'lisatud' väljast."""
    if not e.get("rel") or not e.get("lisatud"):
        return False
    try:
        diff = (date.fromisoformat(TODAY) - date.fromisoformat(e["lisatud"])).days
    except ValueError:
        return False
    return 0 <= diff <= 30


def _is_current(e):
    """Kuulub data.json-i (mitte arhiivi): tulevane, TBA või veel featured-aknas."""
    return bool(e.get("tba")) or _featured(e) or e.get("d", "") >= TODAY


def _load_entries(path):
    if not path.exists():
        return []
    try:
        j = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(j, dict):
        return j.get("entries", [])
    return j if isinstance(j, list) else []


def split_and_write(data_dir, fresh, log=None, block=None, block_names=None):
    """data_dir: Path (nt ROOT/'data' või ROOT/'rap'/'data').
    fresh: sel korral kokku pandud kirjed (manual + värske auto).
    Tagastab (n_current, n_archive)."""
    data_dir = Path(data_dir)
    arch_dir = data_dir / "archive"
    arch_dir.mkdir(exist_ok=True)
    block = block or set()
    block_names = block_names or set()

    # 1) Eelnev seis: eelmine data.json + kõik olemasolevad arhiivifailid
    prev = _load_entries(data_dir / "data.json")
    archived_prev = []
    for f in sorted(arch_dir.glob("[0-9][0-9][0-9][0-9].json")):
        archived_prev.extend(_load_entries(f))

    # 2) Union, prioriteet: fresh > eelmine data.json > arhiiv (esimene võidab)
    seen, allentries = set(), []

    def add(lst, apply_block):
        for e in lst:
            if "d" not in e or "n" not in e:
                continue
            k = _key(e)
            if k in seen:
                continue
            if apply_block and (k in block or _slug(e["n"]) in block_names):
                continue
            seen.add(k)
            allentries.append(e)

    add(fresh, False)         # manual usaldatud; auto juba blocklist-filtreeritud
    add(prev, True)           # säilitatud kirjed: austa blocklisti
    add(archived_prev, True)

    # 3) Partitsioon
    current = [e for e in allentries if _is_current(e)]
    archived = [e for e in allentries if not _is_current(e)]
    current.sort(key=lambda e: e.get("d", ""))

    # 4) data.json (tulevased + featured)
    out = {"updated": TODAY, "entries": current}
    if log is not None:
        out["log"] = log
    (data_dir / "data.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # 5) Arhiiv aastate kaupa (akumuleeruv dedup-liit, värskem võidab)
    by_year = {}
    for e in archived:
        y = e.get("d", "")[:4]
        if len(y) == 4 and y.isdigit():
            by_year.setdefault(y, []).append(e)

    existing = {f.stem for f in arch_dir.glob("[0-9][0-9][0-9][0-9].json")}
    years_reg = []
    for y in sorted(existing | set(by_year)):
        yfile = arch_dir / f"{y}.json"
        merged = {_key(e): e for e in _load_entries(yfile)}
        for e in by_year.get(y, []):
            merged[_key(e)] = e
        entries = sorted(merged.values(), key=lambda e: e.get("d", ""))
        yfile.write_text(json.dumps({"year": int(y), "entries": entries},
                                    ensure_ascii=False, indent=1), encoding="utf-8")
        months = sorted({e["d"][5:7] for e in entries if len(e.get("d", "")) >= 7})
        years_reg.append({"year": int(y), "count": len(entries), "months": months})

    years_reg.sort(key=lambda x: x["year"], reverse=True)
    (arch_dir / "years.json").write_text(
        json.dumps({"updated": TODAY, "years": years_reg}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return len(current), len(archived)
