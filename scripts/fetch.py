#!/usr/bin/env python3
"""skene.info andmekorje: masinloetavad allikad -> data/data.json

Kihid:
  data/manual.json  - kureeritud kirjed (FB leiud, festivalid, reliisid). EI kirjutata ule.
  auto              - Metal Storm, The Krypt, Paavli, Helitehas (filtreeritud)
Dedup: sama kuupaev + kattuv nimi/band => manual voidab.
Iga allikas on try/except sees - uhe allika kukkumine ei murra korjet.
"""
import json, re, sys, unicodedata, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = date.today().isoformat()
UA = {"User-Agent": "Mozilla/5.0 (compatible; skene.info korje; +https://www.skene.info)"}

# zhanrifilter segazhanrilistele venue'dele (paavli, helitehas)
KEYW = re.compile(
    r"metal|doom|death|black|thrash|grind|sludge|stoner|hardcore|metalcore|"
    r"deathcore|industrial|ebm|darkwave|gothic|goth\b|noise|drone|post-punk",
    re.I)

def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def slug(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9]+", "", s)

# ---------------- allikad ----------------

def src_metalstorm():
    import html as htmllib
    page = get("https://metalstorm.net/events/events.php?e_where=e.country&e_what=Estonia")
    # segment = sundmuse lingist jargmise sundmuse lingini (bandilingid voivad olla "+ (N)" jatkureas)
    anchors = list(re.finditer(r'<b><a href="/events/event\.php\?event_id=(\d+)">\s*([^<]+?)\s*</a></b>', page))
    out = []
    for i, m in enumerate(anchors):
        eid, title = m.group(1), htmllib.unescape(m.group(2).strip())
        seg = page[m.start():anchors[i + 1].start() if i + 1 < len(anchors) else len(page)]
        if "country-estonia" not in seg:
            continue
        dm = re.search(r'<span class="dark">\s*(\d{2})\.(\d{2})\.(\d{4})', seg)
        if not dm:
            continue
        d = f"{dm.group(3)}-{dm.group(2)}-{dm.group(1)}"
        cm = re.search(r'e_where=e\.city&e_what=([^"]+)"', seg)
        city_raw = urllib.parse.unquote(cm.group(1)) if cm else ""
        city = city_raw if city_raw in ("Tallinn", "Tartu") else "mujal"
        vm = re.findall(r'<span class="dark">([^<]+)</span>', seg)
        venue = next((v.strip() for v in vm if not re.match(r"^\d{2}\.\d{2}\.\d{4}", v.strip()) and v.strip() != "-"), "")
        bands = [htmllib.unescape(b.strip()) for b in re.findall(r'band\.php\?band_id=\d+"[^>]*>([^<]+)</a>', seg)]
        # pealkirjast "Band: Tour Name" -> lyhem nimi
        name = title.split(":")[0].strip() if bands and title.lower().startswith(bands[0].lower()) else title
        out.append({"d": d, "t": "kontsert", "n": name, "b": bands, "v": venue or "TBA",
                    "c": city, "g": ["metal"], "sn": "Metal Storm",
                    "su": f"https://metalstorm.net/events/event.php?event_id={eid}"})
    return out

def src_krypt():
    # proovi nii stabiilset kui eksperimentaalset endpoint'i
    for url, hdr in [
        ("https://www.thekrypt.ee/wp-json/tribe/events/v1/events?per_page=50", {}),
        ("https://www.thekrypt.ee/wp-json/tec/v1/events?per_page=50", {"X-TEC-EEA": "true"}),
    ]:
        try:
            req = urllib.request.Request(url, headers={**UA, **hdr})
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read().decode())
            events = data.get("events", data if isinstance(data, list) else [])
            out = []
            for e in events:
                start = (e.get("start_date") or e.get("utc_start_date") or "")[:10]
                title = e.get("title", "")
                if isinstance(title, dict):
                    title = title.get("rendered", "")
                title = re.sub(r"<[^>]+>", "", title).strip()
                if not start or not title:
                    continue
                out.append({"d": start, "t": "kontsert", "n": title, "b": [],
                            "v": "The Krypt", "c": "Tallinn", "g": ["metal"],
                            "sn": "thekrypt.ee", "su": e.get("url") or e.get("link") or "https://www.thekrypt.ee/events",
                            "on_": "thekrypt.ee", "ou": "https://www.thekrypt.ee/events"})
            if out:
                return out
        except Exception:
            continue
    return []

def _wp_venue(html, base, venue, city, orgname, orgurl, link_pat):
    """paavli/helitehas: leia sundmuse lingid + kuupaevad lehe HTML-ist, filtreeri zhanri jargi."""
    out = []
    for m in re.finditer(link_pat, html):
        url = m.group(0)
        seg = html[max(0, m.start() - 3000):m.end() + 3000]
        tm = re.search(r'title="([^"]{4,120})"', seg) or re.search(r">([^<>]{6,120})</h\d>", seg)
        title = (tm.group(1) if tm else url.rstrip("/").split("/")[-1].replace("-", " ")).strip()
        title = re.sub(r"&#?\w+;", " ", title).strip()
        if len(re.sub(r"[^A-Za-zÀ-ž]", "", title)) < 4:
            continue
        if not KEYW.search(title) and not KEYW.search(seg[:1500]):
            continue
        dm = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", seg)
        if not dm:
            continue
        d = f"{dm.group(3)}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}"
        out.append({"d": d, "t": "kontsert", "n": title, "b": [], "v": venue, "c": city,
                    "g": ["metal"], "sn": orgname, "su": url, "on_": orgname, "ou": orgurl})
    return out

def src_paavli():
    html = get("https://paavli.ee/sundmused/")
    return _wp_venue(html, "paavli.ee", "Paavli Kultuurivabrik", "Tallinn",
                     "paavli.ee", "https://paavli.ee/sundmused/",
                     r"https://paavli\.ee/sundmused/[a-z0-9%\-\.]+/")

def src_helitehas():
    html = get("https://helitehas.ee/")
    return _wp_venue(html, "helitehas.ee", "Helitehas", "Tallinn",
                     "helitehas.ee", "https://helitehas.ee/",
                     r"https://helitehas\.ee/facebook-event/[a-z0-9%\-\.]+/")

SOURCES = [("metalstorm", src_metalstorm), ("krypt", src_krypt),
           ("paavli", src_paavli), ("helitehas", src_helitehas)]

# ---------------- merge ----------------

def main():
    manual = json.loads((ROOT / "data" / "manual.json").read_text(encoding="utf-8"))
    blockfile = ROOT / "data" / "blocklist.json"
    blockraw = json.loads(blockfile.read_text(encoding="utf-8")) if blockfile.exists() else []
    block = {(b["d"], slug(b["n"])) for b in blockraw if "d" in b}
    block_names = {slug(b["n"]) for b in blockraw if "d" not in b}  # daatumita = blokeeri nimi igal kuupaeval
    auto, log = [], []
    for name, fn in SOURCES:
        try:
            rows = fn()
            log.append(f"{name}: {len(rows)}")
            auto.extend(rows)
        except Exception as ex:
            log.append(f"{name}: VIGA {type(ex).__name__}: {ex}")

    # dedup: manual voidab; auto-kirje kattub kui sama kuupaev JA (nime overlap voi bandi overlap)
    def key_bands(e):
        return {slug(b) for b in e.get("b", []) if b}

    merged = list(manual)
    known = [(e["d"], slug(e["n"]), key_bands(e)) for e in manual]
    seen_auto = set()
    for e in auto:
        if e["d"] < TODAY:
            continue
        k = (e["d"], slug(e["n"]))
        if k in seen_auto or k in block or slug(e["n"]) in block_names:
            continue
        dup = False
        for (d, n, bs) in known:
            if d != e["d"]:
                continue
            en, ebs = slug(e["n"]), key_bands(e)
            if en in n or n in en or (bs & ebs):
                dup = True
                break
        if not dup:
            merged.append(e)
            seen_auto.add(k)

    merged.sort(key=lambda e: e["d"])
    out = {"updated": TODAY, "log": log, "entries": merged}
    (ROOT / "data" / "data.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("; ".join(log))
    print(f"manual {len(manual)} + auto uusi {len(merged) - len(manual)} = {len(merged)}")

if __name__ == "__main__":
    main()
# EOF
