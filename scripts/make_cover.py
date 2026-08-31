#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_cover.py -- jagamispildid (og:image) kolmele saidile.

MIKS (Silveri leid 31.08.2026): kui saata kellelegi link, naitas eelvaade vana
kujundust. Pohjus EI OLNUD vahemalu: `icons/cover.png` oli 05.07.2026 failina alles
(hele vana palett) ja KOIK KOLM saiti osutasid uhele ja samale failile -- seega
rap.skene.info eelvaates seisis samuti "SKENE.INFO".

MIDA: renderdab sama kujundusega, mis `make_weekly_image.py` plakatipea ja mis saidi
enda pais -- tume tint-taust, logo, zanrisonad (aktiivne sait hele, teised tuhmid),
kicker-rida. Kolm faili:
    icons/cover.png        (www)     icons/cover-rap.png     icons/cover-klubi.png
Mootmed 1640x624 = sama mis vanal failil ja OG-meta arvudel templates'is.

Kasutus:
    python scripts/make_cover.py                 # koik kolm
    python scripts/make_cover.py --sait rap      # ainult uks
    python scripts/make_cover.py --logo v5       # kindel logovariant (vaikimisi v1)

PARAST: build_pages.py (og:image tee tuleb templates'ist) + commit + push. Seejarel
KOHUSTUSLIK samm: Facebooki Sharing Debugger (developers.facebook.com/tools/debug/) ->
"Scrape Again" koigile kolmele URL-ile, muidu jaab Messengeri/FB vahemallu vana pilt
veel nadalateks. Sama teeb LinkedIn Post Inspector; Telegram/Signal uuendavad ise.
"""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_DIR = os.path.join(ROOT, "scripts", "assets", "logo")
OUT_DIR = os.path.join(ROOT, "icons")

W, H = 1640, 624

# --- palett: 1:1 make_weekly_image.py-st ---
PABER = (0xF3, 0xF0, 0xE7)
TINT = (0x1A, 0x1A, 0x1A)
HDRMUTED = (0xA6, 0xA1, 0x92)
CAT_ORDER = ["metal", "rap", "klubi"]
CAT_BRIGHT = {"metal": (0xD9, 0x6A, 0x52), "rap": (0x6E, 0x9B, 0xE0), "klubi": (0xA8, 0x7F, 0xE8)}
CAT_DIM = {"metal": (0x70, 0x3E, 0x33), "rap": (0x40, 0x54, 0x73), "klubi": (0x5A, 0x47, 0x77)}
CAT_WORD = {"metal": "METAL", "rap": "RAP", "klubi": "KLUBI"}

# sait -> (failinimi, domeen, esile tostetud kategooria(d), alarida)
SAIDID = {
    "www": ("cover.png", "SKENE.INFO", ["metal", "rap", "klubi"],
            "üritused · merch · reliisid — ühest kohast"),
    "rap": ("cover-rap.png", "RAP.SKENE.INFO", ["rap"],
            "eesti räpp ja hip-hop — üritused, merch, reliisid"),
    "klubi": ("cover-klubi.png", "KLUBI.SKENE.INFO", ["klubi"],
              "klubikultuur ja elektroonika — üritused ja reliisid"),
}


def _font(cands, size):
    for p in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


SANS_B = ["C:/Windows/Fonts/arialbd.ttf",
          "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
MONO_R = ["C:/Windows/Fonts/consola.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
          "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf"]
MONO_B = ["C:/Windows/Fonts/consolab.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
          "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf"]


def tint_logo(path, size, colour):
    """Sama loogika mis make_weekly_image.tint_logo: must tint -> antud varv."""
    im = Image.open(path).convert("RGBA")
    r, g, b, a = im.split()
    ink = ImageOps.invert(Image.merge("RGB", (r, g, b)).convert("L"))
    mask = ImageChops.multiply(ink, a)
    out = Image.new("RGBA", im.size, colour + (0,))
    out.putalpha(mask)
    return out.resize((size, size), Image.LANCZOS)


def render(sait, logo_variant):
    failinimi, domeen, esile, alarida = SAIDID[sait]
    img = Image.new("RGB", (W, H), TINT)
    d = ImageDraw.Draw(img)

    f_word = _font(SANS_B, 96)
    f_dom = _font(MONO_B, 40)
    f_sub = _font(MONO_R, 30)
    f_foot = _font(MONO_R, 26)

    M = 96
    logo_size = 168
    # TOP nihutab kogu ploki vertikaalselt keskele (jaluse joone kohal olevas alas).
    # Ilma selleta istub sisu ulemises kolmandikus ja alumine pool jaab tuhi.
    TOP = 128
    logo_path = os.path.join(LOGO_DIR, logo_variant + ".png")
    if os.path.exists(logo_path):
        img.paste(tint_logo(logo_path, logo_size, PABER), (M, TOP - 2),
                  tint_logo(logo_path, logo_size, PABER))

    x0 = M + logo_size + 44

    # domeeninimi (see rida ERISTAB kolme saiti eelvaates)
    d.text((x0, TOP + 16), domeen, font=f_dom, fill=PABER)

    # zanrisonad: selle saidi oma(d) heledad, ulejaanud tuhmid
    gx = x0
    gy = TOP + 80
    for c in CAT_ORDER:
        col = (CAT_BRIGHT if c in esile else CAT_DIM)[c]
        d.text((gx, gy), CAT_WORD[c], font=f_word, fill=col)
        gx += d.textlength(CAT_WORD[c], font=f_word) + 34

    # alarida
    d.text((x0, gy + 132), alarida, font=f_sub, fill=HDRMUTED)

    # joon + jalus
    jy = H - 118
    d.line([(M, jy), (W - M, jy)], fill=(0x3A, 0x38, 0x33), width=2)
    d.text((M, jy + 30), "eesti alternatiiv  ▪  üks võrgustik", font=f_foot, fill=HDRMUTED)
    tekst = "skene.info"
    d.text((W - M - d.textlength(tekst, font=f_dom), jy + 20), tekst, font=f_dom, fill=PABER)

    os.makedirs(OUT_DIR, exist_ok=True)
    tee = os.path.join(OUT_DIR, failinimi)
    img.save(tee, "PNG", optimize=True)
    return tee, os.path.getsize(tee)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sait", choices=list(SAIDID) + ["koik"], default="koik")
    ap.add_argument("--logo", default="v1", help="logovariant scripts/assets/logo-st")
    a = ap.parse_args()
    saidid = list(SAIDID) if a.sait == "koik" else [a.sait]
    for s in saidid:
        tee, suurus = render(s, a.logo)
        print("OK %-6s -> %s (%d B, %dx%d)" % (s, os.path.relpath(tee, ROOT), suurus, W, H))
    print("\nJARGMISEKS: python scripts/build_pages.py  (og:image tee tuleb templates'ist),"
          "\nsiis commit+push, siis Facebooki Sharing Debuggeris 'Scrape Again' koigile kolmele.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
