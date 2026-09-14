#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_mail_logos.py -- teeb uudiskirja paise jaoks veebis serveeritavad logofailid.

Uudiskirja pais on tume (TINT #1A1A1A) ja meilikliendid ei oska SVG-d ega
laadi kirja sisse `scripts/assets/` faile -- logo peab olema PNG-na saidil.
Allikas on samad valmiskarvitud logod, mida kasutab pildigeneraator:
  scripts/assets/logo/sait-<sait>.png  -> "+" on saidi enda varvis
  scripts/assets/logo/vorgustik.png    -> valge "+" (mitme teemaga kiri)
(brand 09.2026 reegel: vorgustiku kohtades valge pluss, saidi kohtades saidi varv)

Valjund: icons/mail-logo-{metal,rap,klubi,vorgustik}.png, 128x128, alfa
LAMESTATUD tumedale taustale -- vana Outlook ei renderda labipaistvust.

Jooksuta uuesti ainult siis, kui logo ise muutub.
"""
import os
from PIL import Image

TINT = (26, 26, 26)
SIZE = 128

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "assets", "logo")
DST = os.path.join(ROOT, "icons")

VARIANDID = {
    "metal": "sait-metal.png",
    "rap": "sait-rap.png",
    "klubi": "sait-klubi.png",
    "vorgustik": "vorgustik.png",
}


def main():
    for nimi, fail in VARIANDID.items():
        sp = os.path.join(SRC, fail)
        if not os.path.exists(sp):
            raise SystemExit("puudub: " + sp)
        logo = Image.open(sp).convert("RGBA").resize((SIZE, SIZE), Image.LANCZOS)
        taust = Image.new("RGBA", (SIZE, SIZE), TINT + (255,))
        taust.alpha_composite(logo)
        vp = os.path.join(DST, f"mail-logo-{nimi}.png")
        taust.convert("RGB").save(vp, "PNG", optimize=True)
        print("kirjutatud:", os.path.relpath(vp, ROOT))


if __name__ == "__main__":
    main()
