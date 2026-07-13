#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
classify.py — skene.info žanri/subdomeeni kontrollskript.

Jookseb pärast iganädalast sweep'i ja kontrollib, kas www/rap/klubi
manual.json failidesse lisatud kirjed on tõesti õiges subdomeenis,
vaadates artistide žanrisilte Last.fm'ist ja MusicBrainz'ist.

Skript EI LIIGUTA ega MUUDA kirjeid — see ainult raporteerib.

Kasutus (repo juurest):
    python scripts/classify.py
    python scripts/classify.py --all
    python scripts/classify.py --refresh --verbose
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Žanrisiltide -> subdomeeni võtmesõnade tabelid.
# Kontrollijärjekord on TÄHTIS: RAP enne WWW-d enne KLUBI't, sest
# näiteks "industrial metal" peab tabama WWW-d (metal võidab), mitte
# KLUBI't ("industrial" on nõrk klubi-signaal ainult siis, kui ükski
# tugevam sõna ei tabanud).
# ---------------------------------------------------------------------------

RAP_SIGNALS = [
    "hip hop", "hip-hop", "rap", "trap", "grime", "boom bap", "drill",
]

WWW_SIGNALS = [
    "metal", "rock", "punk", "hardcore", "grindcore", "grind", "doom",
    "sludge", "thrash", "death", "black metal", "crust", "screamo",
    "emo", "shoegaze", "post-punk", "gothic rock", "stoner", "core",
]

KLUBI_SIGNALS = [
    "techno", "house", "drum and bass", "dnb", "jungle", "bass music",
    "dubstep", "ebm", "aggrotech", "dark electro", "electro-industrial",
    "darkwave", "synthpop", "electropop", "idm", "ambient", "electronic",
    "electro", "trance", "hardstyle", "footwork", "breakbeat", "industrial",
]

SUFFIX_RE = re.compile(r"\s*\([A-Z]{2,4}\)\s*$")

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"
MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/artist/"
MB_USER_AGENT = "skene.info-classify/1.0 (skene.info@agentmail.to)"


def strip_suffix(name):
    """Eemaldab bändinimelt riigikoodi sufiksi, nt 'AJO (FIN)' -> 'AJO'."""
    if not name:
        return name
    return SUFFIX_RE.sub("", name).strip()


def classify_tag(tag):
    """Määrab ühe žanrisildi bucket'i: 'rap' / 'www' / 'klubi' / None."""
    t = tag.lower()
    for kw in RAP_SIGNALS:
        if kw in t:
            return "rap"
    for kw in WWW_SIGNALS:
        if kw in t:
            return "www"
    for kw in KLUBI_SIGNALS:
        if kw in t:
            return "klubi"
    return None


def classify_tags(tags):
    """
    Kaalutud hääletus žanrisiltide üle.
    Sildid on populaarsuse järjekorras, kaal = max(1, 8 - indeks).
    Domeen otsustatakse, kui võitja bucket saab >= 60% kogukaalust.
    Tagastab (domeen, evidence) kus evidence = {"rap": [...], "www": [...], "klubi": [...]}.
    """
    evidence = {"rap": [], "www": [], "klubi": []}
    if not tags:
        return "unknown", evidence

    weights = {"rap": 0.0, "www": 0.0, "klubi": 0.0}
    total = 0.0
    for i, tag in enumerate(tags):
        w = max(1, 8 - i)
        bucket = classify_tag(tag)
        if bucket:
            weights[bucket] += w
            evidence[bucket].append(tag)
            total += w

    if total == 0:
        return "unclear", evidence

    winner = max(weights, key=weights.get)
    if weights[winner] >= 0.6 * total:
        return winner, evidence
    return "unclear", evidence


# ---------------------------------------------------------------------------
# Välised päringud (Last.fm, MusicBrainz)
# ---------------------------------------------------------------------------

def safe_http_get_json(url, headers=None, timeout=10):
    """Teeb HTTP GET päringu ja parsib JSON'i. Vigade korral tagastab None, ei kraki."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            json.JSONDecodeError, OSError, ValueError):
        return None


def lastfm_lookup(artist, api_key):
    """Last.fm artist.getTopTags. Hoiab sildid, mille count >= 10, max 8 tk."""
    params = {
        "method": "artist.gettoptags",
        "artist": artist,
        "api_key": api_key,
        "format": "json",
        "autocorrect": "1",
    }
    url = LASTFM_URL + "?" + urllib.parse.urlencode(params)
    data = safe_http_get_json(url)
    time.sleep(0.3)
    if not data:
        return []
    try:
        raw_tags = data.get("toptags", {}).get("tag", [])
    except AttributeError:
        return []
    if isinstance(raw_tags, dict):
        raw_tags = [raw_tags]

    tags = []
    for t in raw_tags:
        try:
            count = int(t.get("count", 0))
        except (TypeError, ValueError):
            count = 0
        name = (t.get("name") or "").strip().lower()
        if count >= 10 and name:
            tags.append(name)
        if len(tags) >= 8:
            break
    return tags


def musicbrainz_lookup(artist):
    """MusicBrainz artist-otsing. Kasutab ainult esimest tulemust, kui score >= 90."""
    query = "artist:" + artist
    params = {"query": query, "fmt": "json", "limit": "1"}
    url = MUSICBRAINZ_URL + "?" + urllib.parse.urlencode(params)
    headers = {"User-Agent": MB_USER_AGENT}
    data = safe_http_get_json(url, headers=headers)
    time.sleep(1.1)
    if not data:
        return []
    artists = data.get("artists", [])
    if not artists:
        return []
    first = artists[0]
    try:
        score = int(first.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    if score < 90:
        return []
    tags = first.get("tags", []) or []
    names = [(t.get("name") or "").strip().lower() for t in tags if t.get("name")]
    return names[:8]


def lookup_artist(clean_name, args, lastfm_key):
    """Küsib artisti sildid Last.fm'ist, vajadusel MusicBrainz'ist. Ei kraki kunagi."""
    tags = []
    src = "none"

    if lastfm_key:
        try:
            tags = lastfm_lookup(clean_name, lastfm_key)
        except Exception:
            tags = []
        if tags:
            src = "lastfm"

    if not tags:
        try:
            mb_tags = musicbrainz_lookup(clean_name)
        except Exception:
            mb_tags = []
        if mb_tags:
            tags = mb_tags
            src = "musicbrainz"

    if args.verbose:
        print(f"  [otsing] {clean_name}: allikas={src} sildid={tags}")

    return tags, src


def get_lastfm_key(repo_root):
    """Loeb Last.fm API võtme env muutujast või scripts/lastfm_api_key.txt failist."""
    key = os.environ.get("LASTFM_API_KEY")
    if key:
        return key.strip()
    key_path = repo_root / "scripts" / "lastfm_api_key.txt"
    if key_path.exists():
        try:
            with open(key_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                return content
        except Exception:
            pass
    return None


# ---------------------------------------------------------------------------
# Vahemälu (data/artists.json)
# ---------------------------------------------------------------------------

def load_cache(path):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data.get("artists"), dict):
                data["artists"] = {}
            return data
        except Exception:
            pass
    return {"updated": "", "artists": {}}


def save_cache(path, cache, today):
    cache["updated"] = today.isoformat()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception as e:
        print(f"HOIATUS: ei suutnud vahemälu salvestada: {e}")


def resolve_artist(raw_name, cache, args, lastfm_key, today):
    """Tagastab (puhastatud nimi, cache-kirje) ühe artisti kohta, pärides vajadusel."""
    clean = strip_suffix(raw_name)
    if not clean:
        return None

    entry = cache["artists"].get(clean)
    need_query = entry is None

    if entry is not None and args.refresh:
        if args.all:
            need_query = True
        else:
            checked = entry.get("checked", "")
            try:
                checked_date = date.fromisoformat(checked)
                if (today - checked_date).days > 90:
                    need_query = True
            except ValueError:
                need_query = True

    if need_query:
        tags, src = lookup_artist(clean, args, lastfm_key)
        domain, _ = classify_tags(tags)
        cache["artists"][clean] = {
            "tags": tags,
            "domain": domain,
            "src": src,
            "checked": today.isoformat(),
        }
        entry = cache["artists"][clean]

    return clean, entry


# ---------------------------------------------------------------------------
# manual.json failide lugemine ja skoobi määramine
# ---------------------------------------------------------------------------

def load_manual(path):
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"HOIATUS: ei suutnud lugeda faili {path}: {e}")
        return []


def in_scope(entry, today, all_flag):
    """Vaikimisi skoop: kirjed d >= täna, pluss reliisid/merch lisatud >= täna-30p."""
    if all_flag:
        return True

    d = entry.get("d")
    if d:
        try:
            if date.fromisoformat(d) >= today:
                return True
        except ValueError:
            pass

    lisatud = entry.get("lisatud")
    if lisatud:
        try:
            if date.fromisoformat(lisatud) >= today - timedelta(days=30):
                return True
        except ValueError:
            pass

    return False


# ---------------------------------------------------------------------------
# Peavoog
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="skene.info žanri/subdomeeni kontroll pärast sweep'i (raportib, ei muuda midagi)."
    )
    parser.add_argument("--all", action="store_true",
                         help="töötle kõiki kirjeid, mitte ainult viimase perioodi omi")
    parser.add_argument("--refresh", action="store_true",
                         help="uuenda vahemälus üle 90 päeva vanad artistid (koos --all uuendab kõik cache'itud artistid)")
    parser.add_argument("--verbose", action="store_true",
                         help="prindi iga välise päringu tulemus jooksvalt")
    parser.add_argument("--repo", default=None,
                         help="repo juurkataloog (vaikimisi skripti kataloogi ülemkataloog)")
    return parser.parse_args()


def build_report(file_counts, conflicts, unclear_artists, unknown_artists, today):
    lines = []
    lines.append(f"# skene.info žanriklassifikaatori raport — {today.isoformat()}")
    lines.append("")
    lines.append("## Kokkuvõte failide kaupa")
    for domain_name in ("www", "rap", "klubi"):
        counts = file_counts.get(domain_name, {"kokku": 0, "vaates": 0})
        lines.append(f"- {domain_name}: kokku {counts['kokku']} kirjet, vaates {counts['vaates']}")
    lines.append("")

    lines.append(f"## KONFLIKTID ({len(conflicts)})")
    if not conflicts:
        lines.append("Konflikte ei leitud.")
    else:
        for c in conflicts:
            lines.append(
                f"- [{c['file']}] {c['date']} \"{c['entry']}\" → praegu **{c['file']}**, soovitus **{c['suggested']}**"
            )
            for artist, tags in c["evidence"].items():
                tag_str = ", ".join(tags) if tags else "(sildid puuduvad)"
                lines.append(f"    - {artist}: {tag_str}")
    lines.append("")

    lines.append(f"## EBASELGED ({len(unclear_artists)})")
    if not unclear_artists:
        lines.append("Ebaselgeid artiste ei leitud.")
    else:
        for name, tags in sorted(unclear_artists, key=lambda x: x[0]):
            tag_str = ", ".join(tags) if tags else "(sildid puuduvad)"
            lines.append(f"- {name}: {tag_str}")
    lines.append("")

    lines.append(f"## TUNDMATUD ({len(unknown_artists)})")
    if unknown_artists:
        lines.append(", ".join(sorted(unknown_artists)))
    else:
        lines.append("Kõigi artistide kohta leiti välisandmeid.")
    lines.append("")

    return "\n".join(lines)


def main():
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    repo_root = Path(args.repo).resolve() if args.repo else script_dir.parent
    today = date.today()

    files = {
        "www": repo_root / "data" / "manual.json",
        "rap": repo_root / "rap" / "data" / "manual.json",
        "klubi": repo_root / "klubi" / "data" / "manual.json",
    }
    cache_path = repo_root / "data" / "artists.json"
    report_path = repo_root / "sweep" / "classify_report.md"

    cache = load_cache(cache_path)
    lastfm_key = get_lastfm_key(repo_root)
    if lastfm_key is None:
        print("HOIATUS: Last.fm API võtit ei leitud (scripts/lastfm_api_key.txt või LASTFM_API_KEY) — kasutan ainult MusicBrainzi.")

    file_counts = {}
    conflicts = []
    unclear_artists = set()
    unknown_artists = set()

    try:
        for domain_name, path in files.items():
            entries = load_manual(path)
            scoped = [e for e in entries if in_scope(e, today, args.all)]
            file_counts[domain_name] = {"kokku": len(entries), "vaates": len(scoped)}

            for entry in scoped:
                artist_names = entry.get("b") or []
                decided_domains = []
                evidence_map = {}

                for raw in artist_names:
                    result = resolve_artist(raw, cache, args, lastfm_key, today)
                    if result is None:
                        continue
                    clean, art_entry = result
                    a_domain = art_entry.get("domain", "unknown")

                    if a_domain in ("www", "rap", "klubi"):
                        decided_domains.append(a_domain)
                        evidence_map[clean] = art_entry.get("tags", [])
                    elif a_domain == "unclear":
                        unclear_artists.add((clean, tuple(art_entry.get("tags", []))))
                    else:
                        unknown_artists.add(clean)

                if decided_domains:
                    counts = Counter(decided_domains)
                    top_domain, top_count = counts.most_common(1)[0]
                    ties = [d for d, c in counts.items() if c == top_count]
                    if len(ties) == 1 and top_domain != domain_name:
                        conflicts.append({
                            "file": domain_name,
                            "entry": entry.get("n", "?"),
                            "date": entry.get("d", "?"),
                            "suggested": top_domain,
                            "evidence": evidence_map,
                        })
    except Exception as e:
        print(f"VIGA töötlemisel: {e}")
    finally:
        save_cache(cache_path, cache, today)

    report_text = build_report(file_counts, conflicts, unclear_artists, unknown_artists, today)
    print(report_text)

    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
    except Exception as e:
        print(f"HOIATUS: ei suutnud raportit salvestada: {e}")

    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
