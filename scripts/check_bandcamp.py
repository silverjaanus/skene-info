#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_bandcamp.py -- valve: uued albumid sources.json-i Bandcamp-kontodel.

Taust (21.08.2026 audit): Must Missa «Khattra Tapes» jai sweepist kahe silma
vahele, sest Mahtra Records oli sources.json-is ainult FB-URL-iga ja discover-
tag-otsing seda ei naidanud; reliisi puudis kinni Bandcampi fannimeil (juhus).
Label-/artistilehed (erinevalt discover-otsingust) fetchivad serverist
probleemita (kinnitatud 21.08) -- seega saab neid valvata iga paev automaatselt.

Loogika:
 1. Korjab sweep/sources.json-ist KOIK alamdomeenid *.bandcamp.com -- ka
    nb-margetest (nt facecollector on kirjas ainult nb-tekstis). discover-
    otsingud jaavad valja (Cloudflare blokeerib serveri, Chrome-kihi asi).
 2. Fetchib iga konto /music lehe ja loeb albumilinkide loendi.
 3. Vordleb data/bandcamp_seen.json vastu. Tundmatu album -> ALERT + exit 1
    -> Andmekorje workflow laheb punaseks -> GitHub saadab Silverile kirja.
    Punane PUSIB, kuni album on ackitud (sama muster mis check_sweep_varskus).
 4. ACK: kontrolli album ule (kahe allika reegel + Bandcampi kuupaeva-lohks,
    vt sources.json bandcamp_otsing nb), lisa reliisikirje oige saidi
    manual.json-i (rel + lisatud kohustuslikud!) ja lisa albumi URL
    data/bandcamp_seen.json-i SAMAS commitis. Kui otsustad MITTE lisada,
    lisa URL ikkagi seen-faili (see ongi teadlik "ei").

Kasutus:
  python scripts/check_bandcamp.py            # valve (exit 1 kui uusi albumeid)
  python scripts/check_bandcamp.py --seed     # margi KOIK praegused nahtuks
"""
import json, re, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEEN = ROOT / "data" / "bandcamp_seen.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; skene.info korje; +https://www.skene.info)"}

# alamdomeenid, mis EI ole kontod
EI_KONTO = {"www", "bandcamp"}


def kontod():
    """Koik *.bandcamp.com alamdomeenid sources.json-ist (ka nb-tekstidest)."""
    txt = (ROOT / "sweep" / "sources.json").read_text(encoding="utf-8")
    subs = set(re.findall(r"([a-z0-9][a-z0-9-]*)\.bandcamp\.com", txt, re.I))
    return sorted(s.lower() for s in subs if s.lower() not in EI_KONTO)


def albumid(sub):
    """Tagastab (set albumi-URL-e, viga|None) konto /music lehelt."""
    url = "https://%s.bandcamp.com/music" % sub
    try:
        r = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(r, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
    except Exception as ex:
        return set(), "%s: %s" % (type(ex).__name__, ex)
    # Lingid elavad mitmel kujul: href="/album/x", escaped JSON ("\/album\/x"),
    # absoluutsed URL-id ld+json-is. Singlid on /track/ all — ka need on
    # reliisid (21.08 test: fuzzolini /music = 1 album + 4 singlit).
    # NB jutumark prefiksis on kohustuslik: paljas "/album/..." matchiks ka
    # TEISTE kontode absoluutsete URL-ide sabasid (soovitusplokid).
    html = html.replace("\\/", "/")
    out = set()
    for m in re.findall(r'"(/(?:album|track)/[a-zA-Z0-9._~-]+)', html):
        out.add("https://%s.bandcamp.com%s" % (sub, m))
    for m in re.findall(r'"https?://%s\.bandcamp\.com(/(?:album|track)/[a-zA-Z0-9._~-]+)'
                        % re.escape(sub), html):
        out.add("https://%s.bandcamp.com%s" % (sub, m))
    return out, None


def main():
    seed = "--seed" in sys.argv
    seen = set()
    if SEEN.exists():
        seen = set(json.loads(SEEN.read_text(encoding="utf-8")).get("seen", []))
    subs = kontod()
    if not subs:
        print("HOIATUS: sources.json-ist ei leidnud yhtegi bandcamp-kontot")
        return 0
    uued, vead, koik = [], [], set()
    for sub in subs:
        alb, viga = albumid(sub)
        if viga:
            vead.append("%s: %s" % (sub, viga))
            print("HOIATUS: %s.bandcamp.com fetch kukkus (%s)" % (sub, viga))
            continue
        if not alb:
            print("HOIATUS: %s.bandcamp.com/music andis 0 albumit — parser voi leht?" % sub)
        koik |= alb
        uued += sorted(a for a in alb if a not in seen)
        print("%s: %d albumit, %d uut" % (sub, len(alb), len(sorted(a for a in alb if a not in seen))))
    if vead and len(vead) == len(subs):
        print("VIGA: KOIK bandcamp-fetchid kukkusid. Kui see kordub Actionsis mitu "
              "paeva jarjest, blokeerib Cloudflare runneri IP-d ja valve tuleb "
              "Chrome-kihti viia — ara kustuta valvet vaikselt.")
        return 1
    if seed:
        SEEN.write_text(json.dumps(
            {"nb": "check_bandcamp.py ack-nimekiri: siin olev album on labi "
                   "vaadatud (lisatud manual.json-i VOI teadlikult valja jaetud). "
                   "Uus album, mida siin pole -> Andmekorje punane.",
             "seen": sorted(koik | seen)},
            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("SEED: %d albumit margitud nahtuks (%s)" % (len(koik | seen), SEEN))
        return 0
    if uued:
        print("\nALERT: %d uut albumit Bandcampi kontodel:" % len(uued))
        for a in uued:
            print("  UUS: %s" % a)
        print("Kontrolli yle (kahe allika reegel + kuupaeva-lohks, vt sources.json "
              "bandcamp_otsing nb), lisa reliisikirje (rel+lisatud!) oige saidi "
              "manual.json-i ja lisa URL data/bandcamp_seen.json-i. Ka teadlik "
              "valjajatt tuleb seen-faili kirjutada.")
        return 1
    print("Bandcamp: uusi albumeid pole (%d kontot, %d albumit teada)." % (len(subs), len(seen)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
