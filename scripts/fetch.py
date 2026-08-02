#!/usr/bin/env python3
"""skene.info andmekorje: masinloetavad allikad -> data/data.json

Kihid:
  data/manual.json  - kureeritud kirjed (FB leiud, festivalid, reliisid). EI kirjutata ule.
  auto              - Metal Storm, The Krypt, Paavli, Helitehas (filtreeritud)
Dedup: sama kuupaev + kattuv nimi/band => manual voidab.
Iga allikas on try/except sees - uhe allika kukkumine ei murra korjet.
"""
import html, json, re, sys, unicodedata, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (compatible; skene.info korje; +https://www.skene.info)"}
sys.path.insert(0, str(Path(__file__).resolve().parent))
from archive_split import split_and_write
from common import slug, today_local, load_blocklist, is_blocked, warn_unknown_bands

TODAY = today_local().isoformat()

# zhanrifilter segazhanrilistele venue'dele (paavli, helitehas)
KEYW = re.compile(
    r"metal|doom|death|black|thrash|grind|sludge|stoner|hardcore|metalcore|"
    r"deathcore|industrial|ebm|darkwave|gothic|goth\b|noise|drone|post-punk|punk",
    re.I)
# NB: 'rock' ja hargnematu 'core' teadlikult VÄLJAS - liiga hägused segažanri
# venue'de (paavli/helitehas) automaatfiltris (nt "score" sisaldab "core").
# Manuaalses kureerimises (manual.json 'g' väli) on rock/core siiski lubatud sildid.

# Osa saite (nt Metal Storm) blokeerib bot-kujulise User-Agenti 403-ga, kuigi sama URL
# avaneb brauseris probleemideta (kontrollitud 02.08.2026). Sellepärast: 403 korral proovi
# UUESTI tavalise brauseri UA-ga. Viisakas bot-UA jaab esimeseks valikuks.
UA_BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/127.0.0.0 Safari/537.36"}


def get(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as ex:
        if ex.code not in (403, 429):
            raise
        req = urllib.request.Request(url, headers=UA_BROWSER)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")

# Zanri META-vastendus — peab olema syncis index.html/arhiiv.html GENRE_META-ga!
# Modifikaatorid (heavy, stoner, melodic, symphonic, extreme, post, psych, shoegaze) metat ei anna.
GENRE_META = {
    "metal": ["metal"], "death": ["metal"], "black": ["metal"], "thrash": ["metal"],
    "doom": ["metal"], "sludge": ["metal"], "power": ["metal"], "pagan": ["metal"],
    "punk": ["punk"], "post-punk": ["punk"],
    "core": ["core"], "grind": ["core"],
    "rock": ["rock"], "folk": ["folk"], "alt": ["alt"],
    "bluus": ["bluus"], "bluusrock": ["bluus", "rock"], "blues rock": ["bluus", "rock"],
    "dark": ["dark"], "industrial": ["dark"], "ebm": ["dark"], "darkwave": ["dark"],
    "goth": ["dark"], "electro": ["dark"],
    "rokk": ["rock"], "gothic": ["dark"], "dark electro": ["dark"], "synth": ["dark"],
    "hardcore": ["core"], "metalcore": ["metal", "core"], "deathcore": ["metal", "core"],
    "melodeath": ["metal"], "groove": ["metal"], "alt-metal": ["metal"], "rituaal": ["folk"],
}

def warn_meta_fallback(entries):
    """Meta-filtri hooldus: teata kirjetest, mis kukuvad fallback-alt'i (yhestki sildist ei tule
    metat) voi on ilma zanrisiltideta — Silver vaatab nadalasweep'i kokkuvottes yle."""
    try:
        fallback, tagless = [], []
        for e in entries:
            g = e.get("g", [])
            if not g:
                tagless.append(e)
            elif not any(GENRE_META.get(x) for x in g):
                fallback.append(e)
        for e in fallback:
            print(f"META-FALLBACK (kuvatakse alt all): {e.get('d','?')} {e.get('n','?')} — sildid {e.get('g')}")
        if tagless:
            print(f"ilma zanrisiltideta {len(tagless)}: " + ", ".join(e.get("n", "?") for e in tagless))
    except Exception as ex:
        print(f"meta-kontroll vahele jaetud: {type(ex).__name__}: {ex}")

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
                title = html.unescape(unicodedata.normalize("NFKC", title)).strip()
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
    block, block_names, block_artists = load_blocklist(ROOT / "data" / "blocklist.json")
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

    # blocklist kehtib ka manual.json-ile (nt kui kureeritud kirje osutub valeks/duplikaadiks)
    manual_ok = []
    for e in manual:
        if is_blocked(e, block, block_names, block_artists):
            print(f"HOIATUS: manual.json kirje blokitud: {e.get('d','')} {e.get('n','')}")
            continue
        manual_ok.append(e)
    manual = manual_ok

    merged = list(manual)
    known = []
    for e in manual:
        if "d" not in e or "n" not in e:
            print(f"HOIATUS: manual.json kirje ilma d/n-ita: {e}")
            continue
        known.append((e["d"], slug(e["n"]), key_bands(e), slug(e.get("v","") or "")))
    seen_auto = set()
    for e in auto:
        if e["d"] < TODAY:
            continue
        k = (e["d"], slug(e["n"]))
        if k in seen_auto or is_blocked(e, block, block_names, block_artists):
            continue
        dup = False
        for (d, n, bs, vs) in known:
            if d != e["d"]:
                continue
            en, ebs, evs = slug(e["n"]), key_bands(e), slug(e.get("v","") or "")
            if en in n or n in en or (bs & ebs) or (evs and evs == vs):
                dup = True
                break
        if not dup:
            merged.append(e)
            seen_auto.add(k)
            # NB: vastuvoetud auto-kirje laheb ka 'known' hulka, et JARGMINE auto-kirje
            # kontrollitaks TEMA vastu sama hagusa reegliga. Ilma selleta kontrolliti
            # auto-vs-auto ainult tapse (d, nimi) vottega ja sama uritus kahest allikast
            # veidi eri nimega jai saidile TOPELT (02.08.2026: "HAINZ (Kosmikud)
            # akustilise kavaga" Krypti FB-st + "Hainz ... TASUTA" thekrypt.ee-st).
            known.append((e["d"], slug(e["n"]), key_bands(e), slug(e.get("v", "") or "")))

    n_cur, n_arch = split_and_write(ROOT / "data", merged, log=log,
                                    block=block, block_names=block_names,
                                    block_artists=block_artists)
    print("; ".join(log))
    print(f"manual {len(manual)} + auto = {len(merged)}; data.json {n_cur}, arhiiv {n_arch}")
    warn_unknown_bands(ROOT / "data", merged)
    warn_meta_fallback(merged)

    # avalik allikate leht (guarditud: viga siin ei murra korjet)
    try:
        import build_sources
        nm, nr, nk = build_sources.build()
        print(f"allikad: peasait {nm}, rap {nr}, klubi {nk}")
    except Exception as ex:
        print(f"build_sources vahele jaetud: {type(ex).__name__}: {ex}")

    # avalik API (guarditud: viga siin ei murra korjet)
    try:
        import build_api
        n_ev, n_ar = build_api.build()
        print(f"api: events {n_ev}, archive {n_ar}")
    except Exception as ex:
        print(f"build_api vahele jaetud: {type(ex).__name__}: {ex}")

if __name__ == "__main__":
    main()
# EOF
