#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""common.py -- skene.info skriptide jagatud abifunktsioonid.

Kasutavad fetch.py, fetch_rap.py, fetch_klubi.py, archive_split.py,
build_api.py, make_weekly_email.py, make_weekly_image.py.

Siia on tõstetud AINULT loogika, mis oli neis failides identne (või erines
vaid juhuslikult, nt copy-paste). Sisuliselt erinevad variandid (nt
price_text kaks varianti make_weekly_email.py-s ja make_weekly_image.py-s)
on teadlikult oma failides alles -- käitumine ei tohi muutuda.

Skriptid jooksevad nii Windowsis (uv Python 3.11, kohalik test/sweep) kui
GitHub Actionsis (ubuntu, Python 3.12, igapäevane korje). Sellepärast on
today_local() zoneinfo ümber try/except -- Windowsi Python install ei
pruugi Euroopa ajavööndite andmebaasi kaasa tuua, Actionsi ubuntu-image'il
see alati on.
"""
import json, re, sys, unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

# Windowsi konsool on vaikimisi cp1252 -- iga hoiatus, mis sisaldab tapitahti voi
# nt 'c' hacekiga, viskaks UnicodeEncodeError'i. 26.07.2026 leiti, et fetch_klubi.py
# bandikontroll jai tapselt sel pohjusel VAIKSELT vahele ("bands-kontroll vahele
# jaetud: UnicodeEncodeError"). fetch.py-l oli see juba olemas, teistel mitte ->
# nuud saavad koik common'it importivad skriptid selle korraga.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def slug(s):
    """Nime -> võrdluskolvaks: diakriitikud maha, ainult a-z0-9 alles."""
    s = unicodedata.normalize("NFKD", s).lower()
    return re.sub(r"[^a-z0-9]+", "", s)


def today_local():
    """Tänane kuupäev Eesti ajas (date-objekt).

    GitHub Actions jookseb UTC-s -- seal on zoneinfo Euroopa andmebaas
    olemas. Windowsi (uv) Python install ei pruugi seda kaasa tuua; siis
    langeme date.today() peale, mis on Windowsi masinal niikuinii Eesti
    kohalik aeg."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Tallinn")).date()
    except Exception:
        return date.today()


def load_entries(path):
    """Loeb kirjed data.json/arhiivifailist tolerantselt: puuduv fail,
    vigane JSON või vana listi-kujuline fail toovad tühja/vastava listi,
    ei kraki kunagi. path: {"entries": [...]} -dict või paljas list."""
    if not path.exists():
        return []
    try:
        j = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        print(f"HOIATUS: {path} ei parsinud, kasutan tühja")
        return []
    if isinstance(j, dict):
        return j.get("entries", [])
    return j if isinstance(j, list) else []


def load_manual(path):
    """Loeb manual.json-i (kureeritud lähtefail). Vigase JSON-i korral EI
    jätka tühja listiga — see teeks data.json-i tühjaks ja sait kaotaks
    kõik tulevased kirjed. Selle asemel kukub selge veateatega (exit != 0),
    et workflow näitaks punast; teised saidid jätkavad oma sammudes."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as ex:
        raise SystemExit(
            f"VIGA: {path} ei parsinud ({type(ex).__name__}: {ex}). "
            "Paranda JSON kasitsi — korje katkestatud, et mitte tuhja "
            "andmestikuga saiti ule kirjutada.")
    if not isinstance(raw, list):
        raise SystemExit(f"VIGA: {path} pole JSON-list (on {type(raw).__name__}).")
    return raw


def load_blocklist(path):
    """Loeb blocklist.json. Tagastab (block, block_names, block_artists):
      block         = {(kuupäev, slug(nimi))} -- konkreetne kirje kindlal päeval
      block_names   = {slug(nimi)}            -- daatumita kirjed, blokeerivad
                                                  nime IGAL kuupäeval
      block_artists = {slug(artist)}          -- ARTISTIBLOKK: kirje kujul
                                                  {"b": "artisti nimi"} blokeerib
                                                  KÕIK selle artisti kirjed
                                                  (nt artist ei soovi saidil olla)
    Puuduv fail ja n/b-väljata kirjed toovad HOIATUS-printi, ei kraki."""
    path = Path(path)
    if not path.exists():
        print(f"HOIATUS: blocklist.json puudub ({path})")
        return set(), set(), set()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as ex:
        raise SystemExit(
            f"VIGA: {path} ei parsinud ({type(ex).__name__}: {ex}). "
            "Paranda JSON — korje katkestatud, sest ilma blocklistita "
            "tuleksid blokitud kirjed saidile tagasi.")
    for b in raw:
        if "n" not in b and "b" not in b:
            print(f"HOIATUS: blocklist.json kirje ilma n/b-ta: {b}")
    block = {(b["d"], slug(b["n"])) for b in raw if "d" in b and "n" in b}
    block_names = {slug(b["n"]) for b in raw if "d" not in b and "n" in b}
    block_artists = {slug(b["b"]) for b in raw if b.get("b")}
    block_artists.discard("")
    return block, block_names, block_artists


def is_blocked(e, block, block_names, block_artists=None):
    """Kas kirje e on blokitud: (kuupäev, slug(nimi)) blockis, paljas
    slug(nimi) block_names-is VÕI kirje kuulub blokitud artistile. Sama
    semantika kõigis kolmes fetchis ja archive_split.py-s.

    Artistiblokk pihta saab kolmel viisil: (1) artist on kirje `b`-massiivis,
    (2) kirje nimi ON artisti nimi, (3) kirje nimi ALGAB artisti nimega ja
    artisti slug on >= 8 tähemärki (reliisipealkirjad kujul
    'toxic yuri — «there once was a girl»'; pikkusepiir hoiab ära juhusliku
    pihtamise lühikeste nimede puhul)."""
    n = slug(e.get("n", ""))
    if (e.get("d", ""), n) in block or n in block_names:
        return True
    if block_artists:
        if n in block_artists:
            return True
        for b in (e.get("b") or []):
            if slug(b) in block_artists:
                return True
        for a in block_artists:
            if len(a) >= 8 and n.startswith(a):
                return True
    return False


def warn_handover(limit=250):
    """Hoiatab, kui HANDOVER.md on üle limiidi kasvanud (13.08.2026 kärpereegel).
    GitHub Actionsis fail puudub (gitignore'itud) -> vaikib. Kutsub fetch.py."""
    p = Path(__file__).resolve().parent.parent / "HANDOVER.md"
    try:
        n = p.read_text(encoding="utf-8").count("\n")
    except OSError:
        return
    if n > limit:
        print(f"HOIATUS: HANDOVER.md on {n} rida (piir {limit}) — tee kärbe SAMAS "
              "sessioonis: valmis plokid verbatim HANDOVER-ARCHIVE.md lõppu "
              "(vt HANDOVER §2 reegel 10).")


def end_date(e):
    """Ürituse lõppkuupäev ISO-formaadis: d2 ("PP.KK") kui olemas, muidu d.
    Aastavahetust ületav d2 (nt d=30.12, d2=02.01) -> järgmine aasta.
    Vigase d2 korral fallback d peale."""
    d = e.get("d", "")
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})", e.get("d2") or "")
    if not m or len(d) < 10:
        return d
    day, month = int(m.group(1)), int(m.group(2))
    try:
        end = date(int(d[:4]), month, day)
        if end.isoformat() < d:
            end = date(int(d[:4]) + 1, month, day)
    except ValueError:
        return d
    return end.isoformat()


def warn_unknown_bands(data_dir, entries):
    """bands.json hooldus: teata bandidest, keda verifitseeritud linkide
    failis veel pole."""
    try:
        bf = Path(data_dir) / "bands.json"
        known = set(json.loads(bf.read_text(encoding="utf-8")).get("bands", {})) if bf.exists() else set()
        names = {b for e in entries for b in e.get("b", []) if b}
        missing = sorted(names - known)
        if missing:
            print(f"bands.json-ist puudub {len(missing)}: " + ", ".join(missing))
    except Exception as ex:
        print(f"bands-kontroll vahele jaetud: {type(ex).__name__}: {ex}")


# ---- make_weekly_email.py / make_weekly_image.py jagatud loogika ----
# (need olid failides identsed, kaasa arvatud HOIATUS-tekst)

def parse_d(s):
    return date.fromisoformat(s)


def event_span(e):
    """Ürituse (algus, lõpp) date-objektidena. d2 ("PP.KK") olemasolul
    mitmepäevane üritus; aastavahetust ületav d2 -> järgmine aasta."""
    start = parse_d(e["d"])
    if e.get("d2"):
        dd, mm = e["d2"].split(".")
        end = date(start.year, int(mm), int(dd))
        if end < start:
            end = date(start.year + 1, int(mm), int(dd))
        return start, end
    return start, start


def this_and_next_week(ref):
    """See + järgmine nädal: ref-päevast kuni JÄRGMISE kalendrinädala
    pühapäevani."""
    wd = ref.weekday()  # E=0 ... P=6
    return ref, ref + timedelta(days=(13 - wd))


def next_start(e, ref):
    """Kuupaev, mida uudiskirjas/nadalapildil NAIDATA (ISO-string).

    13.08.2026 Silveri parandus: kaimasoleval tuuril/sarjal naita JARGMIST
    toimumiskuupaeva (dd-massiivist), mitte tuuri esimest, mis voib olla
    moodas; dd-ta kaimasoleval vahemikul (nt mitmepaevane festival) naita
    ref-kuupaeva (uritus kestab). Sama funktsioon molemas generaatoris —
    kiri ja pilt ei tohi lahku minna (28.07 in_scope oppetund)."""
    d = e.get("d", "")
    try:
        s, en = event_span(e)
    except Exception:
        return d
    if s < ref <= en:
        tulevased = sorted(x for x in (e.get("dd") or []) if x >= ref.isoformat())
        return tulevased[0] if tulevased else ref.isoformat()
    return d


def in_window(e, ws, we):
    try:
        s, en = event_span(e)
    except (KeyError, ValueError, TypeError):
        print(f"HOIATUS: kirje vigase/puuduva kuupaevaga jaeti aknast valja: {e.get('n','?')} (d={e.get('d','?')!r})")
        return False
    return s <= we and en >= ws


# Eesti linnakategooriad + kategooriate (alamdomeenide) järjekord --
# identsed make_weekly_email.py-s ja make_weekly_image.py-s.
EESTI = {"Tallinn", "Tartu", "mujal"}
CAT_ORDER = ["metal", "rap", "klubi"]


def is_release(e):
    """Kas kirje on reliis voi merch.

    NB reliisidel ja merchil EI OLE asukohta (Silveri otsus 27.07.2026 --
    `c`/`linn` eemaldati koigilt `t:"reliis"` kirjetelt), seega linnafilter
    neile ei rakendu ega tohigi rakenduda.
    """
    return bool(e.get("rel")) or e.get("t") in ("reliis", "merch")


def in_scope(e):
    """Kas kirje kuulub nadalapilti / uudiskirja.

    Eesti uritus (Tallinn/Tartu/mujal) VOI reliis/merch. Ilma reliisi-erandita
    kaob iga reliis vaikselt valja, sest neil pole `c` valja -- see oli viga
    28.07.2026-ni (leitud sweepis, vt HANDOVER sekts 3).
    """
    return e.get("c") in EESTI or is_release(e)


def _cat_rank(e):
    """CAT_ORDER indeks, mis EI kuku tundmatu kategooria peal (vana
    CAT_ORDER.index() viskas ValueError'i)."""
    c = e.get("_cat", "metal")
    return CAT_ORDER.index(c) if c in CAT_ORDER else len(CAT_ORDER)


def order_for_output(entries, ws):
    """AINUS jarjestusloogika kirja, nadalapildi ja captioni jaoks.

    Teeb kolm asja korraga:
      1. maarab `_disp` = next_start() (kaimasolev tuur naitab JARGMIST
         toimumiskuupaeva, mitte moodunud alguskuupaeva);
      2. sordib naidatava kuupaeva jargi;
      3. segab sama paeva kategooriad labisegi (interleave_cats).

    ⚠ 14.08.2026 OPPETUND: need kolm rida olid kopeeritud make_weekly_email.py-sse,
    make_weekly_image.py-sse ja make_weekly_caption.py-sse, AGA send_weekly.py --
    ainus tee, mis jouab pareti tellijani -- sortis ise `d` jargi ja ei seganud
    kategooriaid. Tulemus: 13.08 kuupaevaparandus ja 14.08 interleave testides
    tootasid, aga 14.08 valjalainud kiri oli ikka vale. Kui muudad jarjestust,
    muuda AINULT siin. Vt scripts/check_send_parity.py."""
    for e in entries:
        e["_disp"] = next_start(e, ws)
    entries.sort(key=lambda e: (e.get("_disp") or e.get("d", ""), _cat_rank(e), e.get("t", "")))
    return interleave_cats(entries)


def interleave_cats(entries):
    """Sama (naidatava) kuupaeva sees jarjesta kategooriad LABISEGI (round-robin
    metal -> rap -> klubi -> metal ...), et nimekirja algus annaks labiloike eri
    tuupi uritustest. Eeldab, et sisend on juba sorditud (_disp/d, CAT_ORDER, t),
    nii et iga kategooria sisemine jarjekord sailib. Silveri soov 14.08.2026:
    varem olid sama paeva kirjed plokkidena metal->rap->klubi ja nimekirja algus
    oli uhekulgne."""
    out = []
    _key = lambda e: e.get("_disp") or e.get("d", "")
    i = 0
    n = len(entries)
    while i < n:
        j = i
        while j < n and _key(entries[j]) == _key(entries[i]):
            j += 1
        grp = entries[i:j]
        buckets = {}
        for e in grp:
            buckets.setdefault(e.get("_cat", "metal"), []).append(e)
        order = [c for c in CAT_ORDER if c in buckets]
        k = 0
        while any(buckets[c] for c in order):
            c = order[k % len(order)]
            if buckets[c]:
                out.append(buckets[c].pop(0))
            k += 1
        i = j
    return out
# EOF
