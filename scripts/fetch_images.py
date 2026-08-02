#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Korjab kirjetele pisipildid (og:image) ja salvestab need saidi enda kausta.

  python scripts/fetch_images.py                # koik 3 saiti, ainult puuduvad
  python scripts/fetch_images.py www --dry-run  # ainult peasait, ei kirjuta midagi
  python scripts/fetch_images.py --force        # laeb ka olemasolevad uuesti

Loogika (Silveri otsus 27.07.2026):
  * pilt otsitakse kirje su/ou/pu lehe <meta og:image> pealt, esimene tootav voidab;
  * FACEBOOKI EI kusita (robotid blokitud, URL-id aeguvad, tingimused ei luba);
  * pilti EI kasutata, kui see on LAI banner (laius/korgus > 2.0) voi alla 200 px -
    laia bannerit ei saa ruuduks karpida ilma teksti lohkumata, sellised kirjed
    jaavad genereeritud tuubimargi peale (frontend joonistab selle ise);
  * alles jaav pilt skaleeritakse laiuseni 216 px (3x kuvasuurus), MITTE ules -
    vaiksem originaal salvestatakse oma suuruses; salvestatakse
    WebP-na <sait>/pildid/<slug>.webp; kirjesse laheb suhteline tee "pildid/<slug>.webp".

Kirje valjad: "img" = suhteline tee. Kui tahad kirjelt pildi ara votta ja hoida
seda ka jargmisel korjel eemal, pane "img": "" (tuhi string = teadlik keeld).
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import slug

try:
    from PIL import Image
except ImportError:
    sys.exit("VIGA: Pillow puudub. Paigalda: python -m pip install Pillow")

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (compatible; skene.info pildikorje; +https://www.skene.info)"}
UA_BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/139.0.0.0 Safari/537.36",
              "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
              "Accept-Language": "et-EE,et;q=0.9,en-US;q=0.8,en;q=0.7"}
KATSEID = 5                 # kokku katseid 403/429 korral (vt get())
PAUSID = (3, 5, 8, 12)      # sekundit katsete vahel
SAIDID = {
    "www":   ROOT / "data",
    "rap":   ROOT / "rap" / "data",
    "klubi": ROOT / "klubi" / "data",
}
PILDIKAUST = {
    "www":   ROOT / "pildid",
    "rap":   ROOT / "rap" / "pildid",
    "klubi": ROOT / "klubi" / "pildid",
}
LAIUS = 216                 # 3x kuvasuurus (72 px)
# Pilti EI KARBITA kunagi (frontendil on korgus auto) - seega lai banner ei lohu, ta on
# lihtsalt madal riba. Piir on ainult seal, kus riba muutub liiga oheseks, et midagi naha.
MAX_SUHE = 2.0              # laiem kui see -> jaab tuubimargi peale
# 200 px on ikka veel ~2,8x kuvasuurus (72 px), seega teravusega on korras. Piir oli
# varem 300, mis viskas kaotsi kogu Metal Stormi plakativaramu (nende og:image on
# alati tapselt 200x200). Silveri otsus 02.08.2026: 200 px pilt on parem kui tuubimark.
MIN_KULG = 200              # liiga vaike originaal ei anna teravat pilti
KEELATUD_HOST = ("facebook.com", "fb.me", "fbcdn.net", "instagram.com", "cdninstagram.com")
# Uldpildid, mis EI OLE kirje oma: kui leht ei paku uritusepilti, annab og:image saidi
# enda logo voi sponsori banneri. Need on ara tuntavad URL-i jargi.
KEELATUD_PILT = ("metalstorm.net/images/fb_icon",)

OG = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:og:image(?::secure_url)?|twitter:image)["\'][^>]*>',
    re.I)
SISU = re.compile(r'content=["\']([^"\']+)["\']', re.I)


def keelatud(url):
    host = urllib.parse.urlparse(url or "").netloc.lower()
    return any(k in host for k in KEELATUD_HOST)


def get(url, timeout=20):
    """403/429 korral proovi mitu korda, UA-sid vaheldumisi.

    Metal Storm annab 403 JUHUSLIKULT (mooedetud 02.08.2026: sama URL, 6 paringut
    kummagi paisekomplektiga -> bot-UA labi 2/6, brauseri oma 1/6, labikukkumised
    laibisegamini). UA vahetamine uksi ei aita; ainus toimiv on kordamine pausiga.
    """
    viimane = None
    for katse in range(KATSEID):
        paised = UA if katse % 2 == 0 else UA_BROWSER
        try:
            req = urllib.request.Request(url, headers=paised)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as ex:
            if ex.code not in (403, 429):
                raise
            viimane = ex
            if katse < KATSEID - 1:
                time.sleep(PAUSID[min(katse, len(PAUSID) - 1)])
    raise viimane


def og_image_htmlist(toores, lehe_url):
    """Sama, aga juba alla laetud baitidest - hoiab kokku teise paringu."""
    html = toores.decode("utf-8", "replace")
    for tag in OG.findall(html):
        m = SISU.search(tag)
        if m:
            return urllib.parse.urljoin(lehe_url, m.group(1).strip()), None
    return None, "og:image puudub"


def og_image(lehe_url):
    """Tagastab lehe og:image absoluutse URL-i voi None."""
    try:
        html = get(lehe_url).decode("utf-8", "replace")
    except Exception as ex:
        return None, "%s: %s" % (type(ex).__name__, ex)
    for tag in OG.findall(html):
        m = SISU.search(tag)
        if m:
            return urllib.parse.urljoin(lehe_url, m.group(1).strip()), None
    return None, "og:image puudub"


def sobib(im, kontrolli_suurust=True):
    """kontrolli_suurust=False kasitsi antud failidele - need on teadlik valik,
    ja voivad juba olla valmis skaleeritud (nt 216 px sweepist)."""
    w, h = im.size
    if kontrolli_suurust and w < MIN_KULG and h < MIN_KULG:
        return False, "liiga vaike (%dx%d)" % (w, h)
    if w / float(h) > MAX_SUHE:
        return False, "liiga lai (%dx%d, suhe %.1f) - riba jaaks liiga ohuke" % (w, h, w / float(h))
    return True, ""


def salvesta(im, sihtfail):
    w, h = im.size
    laius = min(LAIUS, w)       # ARA suurenda originaali - 200 px pilt jaaks uduseks
    uus = (laius, max(1, int(round(h * laius / float(w)))))
    im = im.convert("RGB").resize(uus, Image.LANCZOS)
    sihtfail.parent.mkdir(parents=True, exist_ok=True)
    im.save(sihtfail, "WEBP", quality=80, method=5)
    return uus


def kirje_lehed(e):
    """Lehed, kust pilti otsida - eelistusjarjekorras.

    "img_src" = KASITSI antud aadress (Silveri lisatud). See voib olla nii otsene pildi-URL
    kui ka lehe URL; teistest allikatest ei kusita, kui see on olemas. Facebooki lingid on
    ka siin keelatud - FB kaanepildid tuleb salvestada kaega, vt PILDID-SISEND allpool.
    """
    kasitsi = e.get("img_src")
    if kasitsi and not keelatud(kasitsi):
        return [kasitsi]
    return [u for u in (e.get("su"), e.get("ou"), e.get("pu")) if u and not keelatud(u)]


def pilt_urlist(url):
    """Proovib URL-i kaepealt pildina; kui see on leht, otsib og:image.

    Leht laetakse ainult UKS kord (varem kaks: pildikatse + og:image otsing).
    """
    try:
        toores = get(url)
    except Exception as ex:
        return None, "%s: %s" % (type(ex).__name__, ex)
    try:
        return Image.open(BytesIO(toores)), None
    except Exception:
        pass
    pilt_url, pohjus = og_image_htmlist(toores, url)
    if not pilt_url:
        return None, pohjus
    if any(k in pilt_url.lower() for k in KEELATUD_PILT):
        return None, "og:image on saidi uldlogo, mitte kirje pilt"
    return Image.open(BytesIO(get(pilt_url))), None


def sisendkaustast(sait, kirjed, dry=False):
    """pildid-sisend/<slug>.(jpg|png|webp) -> valmis pisipilt.

    See on rada nendele piltidele, mida masin kutte ei saa (Facebooki kaanepildid):
    salvesta pilt kaega, pane failinimeks kirje slug ja jooksuta skript.
    """
    kaust = ROOT / "pildid-sisend"
    if not kaust.exists():
        return 0
    slugid = {}
    for e in kirjed:
        slugid.setdefault(slug(e.get("n", "")), e)
    n = 0
    for f in sorted(kaust.iterdir()):
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        fs = slug(f.stem)
        e = slugid.get(fs)
        if not e:                                  # failinimi voib olla ka algusosa
            sobivad = [(k, v) for k, v in slugid.items() if fs and k.startswith(fs)]
            if len(sobivad) > 1:
                print("  ?? %-52s sobib %d kirjega, tapsusta nime" % (f.name[:52], len(sobivad)))
                continue
            if sobivad:
                fs, e = sobivad[0][0], sobivad[0][1]
        if not e:
            continue
        try:
            im = Image.open(f)
            ok, miks = sobib(im, kontrolli_suurust=False)
            if not ok:
                print("  -- %-52s SISEND: %s" % (e.get("n", "")[:52], miks))
                continue
            siht = PILDIKAUST[sait] / (fs + ".webp")
            if not dry:
                uus = salvesta(im, siht)
                e["img"] = "pildid/%s.webp" % fs
                f.unlink()                       # sisendfail on ara kasutatud
                print("  ++ %-52s SISENDIST %dx%d" % (e.get("n", "")[:52], uus[0], uus[1]))
            n += 1
        except Exception as ex:
            print("  !! %-52s SISEND %s: %s" % (f.name[:52], type(ex).__name__, ex))
    return n


def tootle(sait, dry=False, force=False):
    mfail = SAIDID[sait] / "manual.json"
    if not mfail.exists():
        print("%-6s manual.json puudub, vahele" % sait)
        return
    data = json.loads(mfail.read_text(encoding="utf-8"))
    kirjed = data["entries"] if isinstance(data, dict) else data
    uusi = vahele = vigu = 0
    uusi += sisendkaustast(sait, kirjed, dry=dry)     # kasitsi salvestatud pildid enne
    for e in kirjed:
        if "img" in e and (e["img"] == "" or not force):
            continue                                    # juba olemas voi teadlik keeld
        nimi = e.get("n", "")
        s = slug(nimi) or slug(str(e.get("d", "")))
        siht = PILDIKAUST[sait] / (s + ".webp")
        if siht.exists() and not force:
            try:                                    # katkine/poolik fail -> lae uuesti
                with Image.open(siht) as im0:
                    im0.verify()
                e["img"] = "pildid/%s.webp" % s
                uusi += 1
                continue
            except Exception:
                print("  ~~ %-52s katkine fail, laen uuesti" % nimi[:52])
                siht.unlink(missing_ok=True)
        lehed = kirje_lehed(e)
        if not lehed:
            vahele += 1
            continue
        im = pohjus = None
        for u in lehed:
            try:
                im, pohjus = pilt_urlist(u)
            except Exception as ex:
                im, pohjus = None, "%s: %s" % (type(ex).__name__, ex)
            if im:
                break
        if not im:
            print("  -- %-52s %s" % (nimi[:52], pohjus or "allikat pole"))
            vahele += 1
            continue
        try:
            ok, miks = sobib(im)
            if not ok:
                print("  -- %-52s %s" % (nimi[:52], miks))
                vahele += 1
                continue
            if dry:
                print("  OK %-52s %dx%d" % (nimi[:52], im.size[0], im.size[1]))
                uusi += 1
                continue
            uus = salvesta(im, siht)
            e["img"] = "pildid/%s.webp" % s
            print("  ++ %-52s %dx%d -> %dx%d" % (nimi[:52], im.size[0], im.size[1], uus[0], uus[1]))
            uusi += 1
        except Exception as ex:
            print("  !! %-52s %s: %s" % (nimi[:52], type(ex).__name__, ex))
            vigu += 1
    if not dry:
        mfail.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("%-6s pilte: %d, vahele: %d, vigu: %d%s" % (sait, uusi, vahele, vigu, "  (DRY-RUN)" if dry else ""))


def main():
    argv = [a for a in sys.argv[1:]]
    dry = "--dry-run" in argv
    force = "--force" in argv
    saidid = [a for a in argv if not a.startswith("--")] or list(SAIDID)
    for s in saidid:
        if s not in SAIDID:
            sys.exit("Tundmatu sait: %s (lubatud: %s)" % (s, ", ".join(SAIDID)))
        print("--- %s ---" % s)
        tootle(s, dry=dry, force=force)


if __name__ == "__main__":
    main()
