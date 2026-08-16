#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_features_carousel.py -- IG karussell, mis tutvustab skene.info voimalusi.

Erinevus make_weekly_image.py-st: siin ei ole andmeid. Slaidide sisu on
kaesolevas failis SLIDES-listis kovakodeeritud, sest tegu on kampaaniapostitusega,
mitte iganadalase automaadiga. Pais, palett, fondid ja logo tulevad tahtlikult
sama loogikaga nagu nadalapildil -- kaks eri valjanagemist samal kontol oleks
pooratud brandivaartus.

Kasutus:
  python scripts/make_features_carousel.py
  python scripts/make_features_carousel.py --out postitused/voimalused.jpg

Valjund: postitused/voimalused.jpg, voimalused-2.jpg, ... (1080x1350 JPG).
"""
import argparse, os, random, sys

try:
    from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageOps
except ImportError:
    sys.exit("Vajalik: pip install pillow")

# ---- palett (sama mis make_weekly_image.py; index.html :root) ----
PABER      = (0xF3, 0xF0, 0xE7)
TINT       = (0x1A, 0x1A, 0x1A)
HALL       = (0x5A, 0x56, 0x4C)
TELLISKIVI = (0x93, 0x39, 0x2C)
PLOOM      = (0x4E, 0x42, 0x75)
SINEP      = (0xA8, 0x81, 0x1F)
PAATINA    = (0x2C, 0x5B, 0x54)

HDRMUTED   = (0xA6, 0xA1, 0x92)
CAT_BRIGHT = {"metal": (0xD9, 0x6A, 0x52), "rap": (0x6E, 0x9B, 0xE0), "klubi": (0xA8, 0x7F, 0xE8)}
CAT_WORD   = {"metal": "METAL", "rap": "RAP", "klubi": "KLUBI"}
CAT_ORDER  = ["metal", "rap", "klubi"]

W, H = 1080, 1350
MARGIN = 64
HEAD_H = 176
LOGO_XY = (MARGIN, 38)
LOGO_SIZE = 100
GWORD_X = MARGIN + LOGO_SIZE + 28
GWORD_Y = 40
KICKER_Y = 110

# ---- fondid (sama kandidaadiloetelu mis nadalapildil) ----
SANS_B = ["C:/Windows/Fonts/arialbd.ttf",
          "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
SANS_R = ["C:/Windows/Fonts/arial.ttf",
          "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
MONO_R = ["C:/Windows/Fonts/consola.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
          "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf"]
MONO_B = ["C:/Windows/Fonts/consolab.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
          "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf"]


def _font(cands, size):
    for p in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def load_fonts():
    return {"gword": _font(SANS_B, 54), "kicker": _font(MONO_R, 20),
            "kicker_b": _font(MONO_B, 20),
            "h2": _font(SANS_B, 52), "h2s": _font(SANS_B, 42),
            "sub": _font(MONO_R, 26),
            "lead": _font(SANS_B, 40),
            "body": _font(SANS_R, 33),
            "step_n": _font(MONO_B, 34),
            "note": _font(MONO_R, 24),
            "foot_b": _font(SANS_B, 29), "foot_r": _font(MONO_R, 21)}


def wrap(draw, text, font, maxw):
    """Murrab teksti laiuse jargi. Erinevalt nadalapildist EI karbi -- slaidi
    tekst on kaesolevas failis kirjas, seega ulepikk rida on minu viga, mida
    tuleb naha, mitte vaikselt kolme punktiga ara peita."""
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---- ikoonid ----
# ⚠ ARIALIS JA CONSOLASES EI OLE ★ (U+2605), ▦ (U+25A6) EGA ✉ (U+2709).
# Kontrollitud .notdef-vordlusega: koik kolm tulid tofu-kastina. Saidil need
# margid TOOTAVAD (brauseri fondipinu leiab need mujalt), aga Pillow votab
# tapselt selle uhe faili, mille me talle anname. Seega joonistame nad ise.
# Kui lisad uue margi, KONTROLLI ta enne ule -- tofu-kast slaidil naeb valja
# nagu katkine pilt, mitte nagu disain.
def draw_icon(d, name, x, y, size, colour):
    """Joonistab ikooni ruutu (x, y, size). Vastab saidi margi kujule."""
    s = size
    if name == "star":
        import math
        cx, cy, r = x + s / 2, y + s / 2, s / 2
        pts = []
        for i in range(10):
            ang = math.radians(-90 + i * 36)
            rad = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        d.polygon(pts, fill=colour)
    elif name == "grid":
        d.rectangle([x, y, x + s, y + s], outline=colour, width=3)
        for i in (1, 2):
            d.line([(x + s * i / 3, y), (x + s * i / 3, y + s)], fill=colour, width=2)
            d.line([(x, y + s * i / 3), (x + s, y + s * i / 3)], fill=colour, width=2)
    elif name == "env":
        h = s * 0.72
        top = y + (s - h) / 2
        d.rectangle([x, top, x + s, top + h], outline=colour, width=3)
        d.line([(x, top), (x + s / 2, top + h * 0.62)], fill=colour, width=3)
        d.line([(x + s, top), (x + s / 2, top + h * 0.62)], fill=colour, width=3)
    elif name == "house":
        d.polygon([(x + s / 2, y), (x + s, y + s * 0.45), (x, y + s * 0.45)], outline=colour, width=3)
        d.rectangle([x + s * 0.15, y + s * 0.45, x + s * 0.85, y + s], outline=colour, width=3)
    elif name == "api":
        d.line([(x + s * 0.35, y), (x + s * 0.1, y + s / 2), (x + s * 0.35, y + s)], fill=colour, width=4)
        d.line([(x + s * 0.65, y), (x + s * 0.9, y + s / 2), (x + s * 0.65, y + s)], fill=colour, width=4)


def pick_logo(logo_dir):
    variants = ["v1", "v2", "v5", "v8", "v9", "v10"]
    random.shuffle(variants)
    for v in variants:
        p = os.path.join(logo_dir, f"{v}.png")
        if os.path.exists(p):
            return p
    return None


def tint_logo(path, size, colour):
    im = Image.open(path).convert("RGBA")
    r, g, b, a = im.split()
    ink = ImageOps.invert(Image.merge("RGB", (r, g, b)).convert("L"))
    mask = ImageChops.multiply(ink, a)
    out = Image.new("RGBA", im.size, colour + (0,))
    out.putalpha(mask)
    return out.resize((size, size), Image.LANCZOS)


# ---- slaidide sisu -------------------------------------------------------
# ("b", tekst)  = taane + jutumark, tavaline vaide
# ("s", tekst)  = nummerdatud samm (juhend)
# ("n", tekst)  = markus vaiksemas monos, hallis
# ("l", tekst)  = suur lause (lead), plokki juhatav mote
SLIDES = [
    {
        "title": "MIDA SKENE.INFO OSKAB",
        "sub": "viis asja peale ürituste nimekirja",
        "accent": TINT,
        "body": [
            ("l", "Minu nimekiri", "star"),
            ("l", "Kalender ja MILLAL-filter", "grid"),
            ("l", "Nädalakiri", "env"),
            ("l", "Äpina telefoni", "house"),
            ("l", "Avalik API", "api"),
            ("n", "keri edasi →"),
        ],
    },
    {
        "title": "MINU NIMEKIRI",
        "icon": "star",
        "sub": "pane tähtis kõrvale, enne kui ära unustad",
        "accent": TELLISKIVI,
        "body": [
            ("b", "Iga kirje pealkirja ees on tärn. Vajuta ja kirje läheb sinu nimekirja."),
            ("b", "Nimekirja kohale tekib riba, kust saab „näita ainult neid“."),
            ("b", "Skoobirea RÄPP ja KLUBI nuppudega korjad kõigi kolme saidi kirjed ühte nimekirja."),
            ("n", "Nimekiri elab sinu enda brauseris. Kontot ei ole, meile ei saadeta midagi — aga teises telefonis on ta tühi."),
        ],
    },
    {
        "title": "KALENDER JA „MILLAL“",
        "icon": "grid",
        "sub": "enamik ei tea kuupäeva, vaid tahab teada, mis täna on",
        "accent": PLOOM,
        "body": [
            ("b", "Filtrite esimene rida: TÄNA · SEL NÄDALAVAHETUSEL · JÄRGMISED 7 PÄEVA."),
            ("b", "Külgribas kuu ruudustik. Klõpsa päeval ja näed kogu selle õhtu kava."),
            ("b", "Iga ürituse all on „+ GOOGLE KALENDER“ — üks vajutus ja üritus on su kalendris."),
            ("n", "Filtreeritud vaade läheb aadressiribale, seega „punk Tartus“ on link, mille saab sõbrale saata."),
        ],
    },
    {
        "title": "NÄDALAKIRI",
        "icon": "env",
        "sub": "reede hommikul, ilma et peaksid ise vaatama käima",
        "accent": PAATINA,
        "body": [
            ("b", "Kord nädalas ülevaade tulevastest üritustest ja värsketest reliisidest."),
            ("b", "Vali ise teemad: metal, räpp, klubi. Eesti või inglise keeles."),
            ("b", "Iga kirja jaluses on eelistuste link — teemasid saab ka maha võtta, ilma et peaksid kirjast üldse loobuma."),
            ("n", "Liitumisvorm on esilehe vasakus veerus ja lehe lõpus."),
        ],
    },
    {
        "title": "ÄPINA TELEFONI",
        "icon": "house",
        "sub": "Android · Chrome",
        "accent": SINEP,
        "body": [
            ("l", "Sait käitub pärast paigaldust nagu äpp: oma ikoon, oma aken, ei mingit brauseririba."),
            ("s", "Ava www.skene.info Chrome’is."),
            ("s", "Vajuta paremal üleval ⋮ menüü."),
            ("s", "Vali „Installi äpp“ (või „Lisa avakuvale“)."),
            ("n", "Chrome pakub seda sageli ka ise, riba lehe allservas."),
        ],
    },
    {
        "title": "ÄPINA TELEFONI",
        "icon": "house",
        "sub": "iPhone · Safari",
        "accent": SINEP,
        "body": [
            ("l", "iPhone ise ei paku midagi — pead selle ühe korra käsitsi lisama."),
            ("s", "Ava www.skene.info Safaris."),
            ("s", "Vajuta all keskel Jaga-nuppu (kast, millest tuleb nool välja)."),
            ("s", "Keri menüüs alla ja vali „Lisa avakuvale“."),
            ("s", "Vajuta paremal üleval „Lisa“."),
        ],
    },
    {
        "title": "AVALIK API",
        "icon": "api",
        "sub": "andmed on masinloetavad, võtmeta ja tasuta",
        "accent": HALL,
        "body": [
            ("b", "api/events.json — kõik tulevased üritused, reliisid ja merch."),
            ("b", "api/archive.json — arhiiv."),
            ("b", "Iga kirje ütleb, millise saidi oma ta on, ja viitab algallikale."),
            ("b", "Uueneb iga päev ja iganädalase korje järel."),
            ("n", "Otspunktid, väljade seletused ja kasutusreeglid: skene.info/api.html"),
        ],
    },
    {
        "title": "KÕIK SEE ON TASUTA",
        "sub": "ja jääb tasuta",
        "accent": TELLISKIVI,
        "body": [
            ("l", "Sait on kureeritud, mittekommertslik ja iga kirje viitab alati algallikale."),
            ("b", "Kui su üritus, reliis või merch on puudu — esilehel on vorm, saada tulema."),
            ("b", "Kui midagi on valesti — iga kirje juures on „teata veast“."),
            ("n", "Uuendused kirjas skene.info/changelog.html"),
        ],
    },
]


# ---- renderdus -----------------------------------------------------------
H2_Y = HEAD_H + 40
FOOT_H = 110
BODY_W = W - 2 * MARGIN


def draw_head(img, d, fonts, logo_path):
    """Sama tume plakatipea mis nadalapildil. Koik kolm zanrisona on siin
    heledad: postitus raagib kogu vorgustikust, mitte uhe nadala sisust."""
    d.rectangle([0, 0, W, HEAD_H], fill=TINT)
    if logo_path:
        logo = tint_logo(logo_path, LOGO_SIZE, PABER)
        img.paste(logo, LOGO_XY, logo)
    gx = GWORD_X
    for c in CAT_ORDER:
        d.text((gx, GWORD_Y), CAT_WORD[c], font=fonts["gword"], fill=CAT_BRIGHT[c])
        gx += d.textlength(CAT_WORD[c], font=fonts["gword"]) + 26
    kx = GWORD_X
    d.text((kx, KICKER_Y), "SKENE.INFO", font=fonts["kicker_b"], fill=PABER)
    kx += d.textlength("SKENE.INFO", font=fonts["kicker_b"])
    d.text((kx, KICKER_Y), "  ▪  eesti alternatiiv  ▪  üks võrgustik",
           font=fonts["kicker"], fill=HDRMUTED)


def draw_body(d, fonts, slide, y, accent, dry=False):
    """Joonistab keha ja tagastab lopu-y. dry=True ainult moodab."""
    step_no = 0
    for item in slide["body"]:
        kind, text = item[0], item[1]
        icon = item[2] if len(item) > 2 else None
        if kind == "l":
            ix = MARGIN + (66 if icon else 0)
            for i, ln in enumerate(wrap(d, text, fonts["lead"], BODY_W - (66 if icon else 0))):
                if not dry:
                    if i == 0 and icon:
                        draw_icon(d, icon, MARGIN + 2, y + 6, 40, accent)
                    d.text((ix, y), ln, font=fonts["lead"], fill=TINT)
                y += 52
            y += 28 if icon else 20
        elif kind == "b":
            lines = wrap(d, text, fonts["body"], BODY_W - 46)
            for i, ln in enumerate(lines):
                if not dry:
                    if i == 0:
                        # taidetud ruut, mitte tekstimark: mote-mark "—" istus
                        # tekstirea pohjas ja nagi valja nagu allakriipsutus.
                        d.rectangle([MARGIN + 2, y + 15, MARGIN + 16, y + 29], fill=accent)
                    d.text((MARGIN + 46, y), ln, font=fonts["body"], fill=TINT)
                y += 44
            y += 18
        elif kind == "s":
            step_no += 1
            lines = wrap(d, text, fonts["body"], BODY_W - 70)
            for i, ln in enumerate(lines):
                if not dry:
                    if i == 0:
                        d.text((MARGIN, y - 2), f"{step_no}.", font=fonts["step_n"], fill=accent)
                    d.text((MARGIN + 70, y), ln, font=fonts["body"], fill=TINT)
                y += 44
            y += 18
        elif kind == "n":
            y += 10
            for ln in wrap(d, text, fonts["note"], BODY_W):
                if not dry:
                    d.text((MARGIN, y), ln, font=fonts["note"], fill=HALL)
                y += 34
            y += 12
    return y


def render_slide(slide, page_no, n_pages, logo_path, fonts, out_path):
    img = Image.new("RGB", (W, H), PABER)
    d = ImageDraw.Draw(img)
    accent = slide["accent"]
    draw_head(img, d, fonts, logo_path)

    # pealkiri: vaiksem font, kui suur ei mahu uhele reale
    icon = slide.get("icon")
    tx = MARGIN + (68 if icon else 0)
    tf = fonts["h2"]
    if d.textlength(slide["title"], font=tf) > W - MARGIN - tx:
        tf = fonts["h2s"]
    y = H2_Y
    if icon:
        draw_icon(d, icon, MARGIN + 2, y + 8, 46, accent)
    d.text((tx, y), slide["title"], font=tf, fill=TINT)
    y += 66
    d.text((MARGIN, y), slide["sub"], font=fonts["sub"], fill=accent)
    y += 46
    d.line([(MARGIN, y), (W - MARGIN, y)], fill=TINT, width=3)
    y += 40

    # tsentreeri keha vertikaalselt vaba ruumi sees
    end = draw_body(d, fonts, slide, y, accent, dry=True)
    slack = (H - FOOT_H - 30) - end
    if slack > 0:
        y += min(slack / 2, 110)
    end = draw_body(d, fonts, slide, y, accent)
    if end > H - FOOT_H:
        print(f"  HOIATUS: slaid {page_no} laheb ule aare ({end} > {H - FOOT_H})")

    # jalus
    fy = H - FOOT_H + 20
    d.line([(MARGIN, fy - 22), (W - MARGIN, fy - 22)], fill=TINT, width=3)
    d.text((MARGIN, fy), "skene.info", font=fonts["foot_b"], fill=TINT)
    pg = f"{page_no}/{n_pages}"
    d.text((W - MARGIN - d.textlength(pg, font=fonts["foot_r"]), fy + 6),
           pg, font=fonts["foot_r"], fill=HALL)

    img.save(out_path, "JPEG", quality=92, optimize=True)
    return out_path


def page_path(base, i):
    root, ext = os.path.splitext(base)
    return base if i == 1 else f"{root}-{i}{ext}"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(root, "postitused", "voimalused.jpg"))
    ap.add_argument("--logo-dir", default=os.path.join(here, "assets", "logo"))
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fonts = load_fonts()
    logo_path = pick_logo(args.logo_dir)
    n = len(SLIDES)
    if n > 10:
        sys.exit(f"Instagrami karusselli piir on 10 slaidi, praegu {n}.")
    for i, s in enumerate(SLIDES, start=1):
        p = render_slide(s, i, n, logo_path, fonts, page_path(args.out, i))
        print(f"  {p}")
    print(f"OK: {n} slaidi")


if __name__ == "__main__":
    main()
