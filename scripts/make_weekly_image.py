#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_weekly_image.py -- genereerib skene.info nadalapildi(d) (metal-pool).

Loeb data/data.json, filtreerib tuleva E-P nadala Eesti uritused + reliisid,
renderdab 1080x1350 JPG(d) saidi varvipaletiga, logo nurgas juhuslikus variandis.

MITU PILTI (IG karussell): kui koik kirjed uhele pildile ei mahu, tehakse
jargmised lehed samas stiilis: nadal-<kuupaev>.jpg, nadal-<kuupaev>-2.jpg jne
(kuni MAX_PAGES lehte; Instagrami karusselli piir on 10 slaidi).
Lehekyljenumber (nt 2/3) kuvatakse alapealkirja real, kui lehti on >1.

Kasutus:
  python scripts/make_weekly_image.py                      # tulev E-P nadal
  python scripts/make_weekly_image.py --date 2026-07-13    # ref-kuupaev (test)
  python scripts/make_weekly_image.py --from 2026-07-13 --days 7
  python scripts/make_weekly_image.py --data data/data.json --out postitused/x.jpg

Reeglid (vt PROJEKT.md):
  - Ainult Eesti: c in {Tallinn, Tartu, mujal}. Rahvusvahelised jaavad valja.
  - Hinda EI leiutata: kui 'hind' puudub, jaetakse hinnarida ara.
  - Mahupiir lehe kohta: kuni MAX_ROWS kirjet; ulejaak -> jargmine leht.
    Kui ka MAX_PAGES lehte ei mahuta koike (ebatoenaoline), viimasele lehele
    rida "+N veel skene.info-s".
"""
import argparse, json, os, random, sys, datetime as dt

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Vajalik: pip install pillow")

# ---- palett (index.html :root) ----
PABER      = (0xF3, 0xF0, 0xE7)
TINT       = (0x1A, 0x1A, 0x1A)
HALL       = (0x5A, 0x56, 0x4C)
JOON       = (0x8F, 0x8A, 0x7C)
TELLISKIVI = (0x93, 0x39, 0x2C)   # kontsert
PLOOM      = (0x4E, 0x42, 0x75)   # klubi
SINEP      = (0xA8, 0x81, 0x1F)   # festival
PAATINA    = (0x2C, 0x5B, 0x54)   # reliis / merch

TYPE_COLOR = {"kontsert": TELLISKIVI, "festival": SINEP, "klubi": PLOOM,
              "reliis": PAATINA, "merch": PAATINA}
TYPE_LABEL = {"kontsert": "KONTSERT", "festival": "FESTIVAL", "klubi": "KLUBI",
              "reliis": "UUS RELIIS", "merch": "MERCH"}
EESTI = {"Tallinn", "Tartu", "mujal"}
# kategooria (alamdomeen) varvid + sildid — VARV eristab kategooriat karussellis
CAT_COLOR = {"metal": (0x93,0x39,0x2C), "rap": (0x2E,0x5E,0xAA), "klubi": (0x6E,0x45,0xA8)}
CAT_LABEL_IMG = {"metal":"METAL","rap":"RÄPP","klubi":"KLUBI"}
CAT_ORDER = ["metal","rap","klubi"]
KUUD_GEN = {1:"jaanuar",2:"veebruar",3:"marts",4:"aprill",5:"mai",6:"juuni",
            7:"juuli",8:"august",9:"september",10:"oktoober",11:"november",12:"detsember"}

W, H = 1080, 1350
MARGIN = 64
MAX_ROWS = 7
MAX_PAGES = 10   # Instagrami karusselli piir

X_DATE = MARGIN
X_BODY = MARGIN + 148
X_END = W - MARGIN
BODY_W = X_END - X_BODY

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

def load_fonts():
    return {"eyebrow": _font(MONO_R, 24), "h1": _font(SANS_B, 80),
            "sub": _font(MONO_R, 26), "date": _font(MONO_B, 38),
            "wday": _font(MONO_R, 19), "tag": _font(MONO_B, 18),
            "title": _font(SANS_B, 35), "title_s": _font(SANS_B, 29),
            "bands": _font(MONO_R, 22), "venue": _font(SANS_B, 24),
            "price": _font(MONO_B, 22), "foot_b": _font(SANS_B, 29),
            "foot_r": _font(MONO_R, 21), "more": _font(SANS_B, 29)}

def parse_d(s):
    return dt.date.fromisoformat(s)

def event_span(e):
    start = parse_d(e["d"])
    if e.get("d2"):
        dd, mm = e["d2"].split(".")
        end = dt.date(start.year, int(mm), int(dd))
        if end < start:
            end = dt.date(start.year + 1, int(mm), int(dd))
        return start, end
    return start, start

def this_and_next_week(ref):
    """See + jargmine nadal: tanasest kuni JARGMISE kalendrinadala pyhapaevani."""
    wd = ref.weekday()  # E=0 ... P=6
    end = ref + dt.timedelta(days=(13 - wd))  # selle nadala pyhapaev + 7
    return ref, end

def in_window(e, ws, we):
    s, en = event_span(e)
    return s <= we and en >= ws

def wrap(draw, text, font, maxw, max_lines):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    lines = lines[:max_lines]
    if lines and draw.textlength(lines[-1], font=font) > maxw:
        s = lines[-1]
        while s and draw.textlength(s + "...", font=font) > maxw:
            s = s[:-1]
        lines[-1] = s + "..."
    return lines

def ellip(draw, text, font, maxw):
    if draw.textlength(text, font=font) <= maxw:
        return text
    while text and draw.textlength(text + "...", font=font) > maxw:
        text = text[:-1]
    return text + "..."

def price_text(e):
    """Luhike hind pildile: ainult 'praegu' number, verbose 'mark' jaetakse valja."""
    h = e.get("hind")
    if not h:
        return None
    p = (h.get("praegu") or "").strip()
    for sep in [";", " — ", " - ", " / ", ",", " ("]:
        if sep in p:
            p = p.split(sep)[0].strip()
    if not p:
        return None
    if h.get("kuni") and h.get("jargmine"):
        return f"{p} → {h['jargmine']}"
    return p

# ---- lehe geomeetria (jagatud mootmise ja renderdamise vahel) ----
FOOT_H = 120
SUB_Y = 82 + 84 + 88
TOP = SUB_Y + 46
START_Y = TOP + 8
ROW_LIMIT = (H - FOOT_H) - 16

def measure(d, fonts, e):
    """Uhe kirje rea korgus + ettearvutatud kujundus (font, pealkirjaread, bandid)."""
    tf = fonts["title"] if len(e.get("n", "")) < 40 else fonts["title_s"]
    tlines = wrap(d, e.get("n", ""), tf, BODY_W, 2)
    bands = " · ".join(e.get("b", [])) if e.get("b") else e.get("a", "")
    h = 30 + len(tlines) * (tf.size + 3)
    if bands:
        h += fonts["bands"].size + 8
    h += fonts["venue"].size + 6
    return max(h, 70) + 16, tf, tlines, bands

def paginate(d, fonts, entries):
    """Jaga kirjed lehtedeks: igal lehel kuni MAX_ROWS kirjet, mis korguselt mahuvad."""
    pages, cur, used = [], [], 0
    for e in entries:
        rh, tf, tlines, bands = measure(d, fonts, e)
        if cur and (len(cur) >= MAX_ROWS or START_Y + used + rh > ROW_LIMIT):
            pages.append(cur)
            cur, used = [], 0
        cur.append([e, rh, tf, tlines, bands])
        used += rh
    if cur:
        pages.append(cur)
    return pages

def pick_logo(logo_dir):
    variants = ["v1", "v2", "v5", "v8", "v9", "v10"]
    random.shuffle(variants)
    for v in variants:
        p = os.path.join(logo_dir, f"{v}.png")
        if os.path.exists(p):
            return p
    return None

def render_page(rows, ws, we, total_n, page_no, n_pages, logo_path, out_path,
                fonts, overflow=0):
    img = Image.new("RGB", (W, H), PABER)
    d = ImageDraw.Draw(img)

    # ---- pais ----
    d.text((MARGIN, 48), "SKENE.INFO  ·  EESTI ALTERNATIIV", font=fonts["eyebrow"], fill=HALL)
    d.text((MARGIN, 82), "TULEVAD", font=fonts["h1"], fill=TINT)
    d.text((MARGIN, 82 + 84), "ÜRITUSED", font=fonts["h1"], fill=TINT)
    if ws.month == we.month:
        rng = f"{ws.day}.–{we.day}. {KUUD_GEN[ws.month]} {we.year}"
    else:
        rng = f"{ws.day}. {KUUD_GEN[ws.month]} – {we.day}. {KUUD_GEN[we.month]} {we.year}"
    sub = f"{rng}  ·  {total_n} kirje" + ("" if total_n == 1 else "t")
    if n_pages > 1:
        sub += f"  ·  {page_no}/{n_pages}"
    d.text((MARGIN, SUB_Y), sub, font=fonts["sub"], fill=TELLISKIVI)

    # ---- logo nurka (sama variant koigil lehtedel) ----
    if logo_path:
        logo = Image.open(logo_path).convert("RGBA").resize((128, 128), Image.LANCZOS)
        img.paste(logo, (W - MARGIN - 128, 52), logo)

    d.line([(MARGIN, TOP), (W - MARGIN, TOP)], fill=TINT, width=3)

    used = sum(r[1] for r in rows)

    # jaota vaba ruum ridade vahele (tasakaal, kui pole overflow'i)
    slack = ROW_LIMIT - (START_Y + used)
    gap = 0
    if overflow == 0 and len(rows) > 0 and slack > 0:
        gap = min(slack / len(rows), 46)

    WDAY = ["E", "T", "K", "N", "R", "L", "P"]
    y = START_Y
    for e, rh, tf, tlines, bands in rows:
        ry = int(y + gap * 0.35)
        s, en = event_span(e)
        col = CAT_COLOR.get(e.get("_cat"), HALL)

        d.text((X_DATE, ry + 2), f"{s.day:02d}.{s.month:02d}", font=fonts["date"], fill=TINT)
        if e.get("t") in ("reliis", "merch") or e.get("rel"):
            d.text((X_DATE, ry + 44), e.get("t", "reliis"), font=fonts["wday"], fill=col)
        else:
            wl = WDAY[s.weekday()]
            if e.get("d2"):
                wl += f" – {en.day:02d}.{en.month:02d}"
            d.text((X_DATE, ry + 44), wl, font=fonts["wday"], fill=HALL)

        lbl = CAT_LABEL_IMG.get(e.get("_cat"), e.get("_cat", "").upper())
        tw2 = d.textlength(lbl, font=fonts["tag"])
        d.rectangle([X_BODY, ry, X_BODY + tw2 + 16, ry + 25], fill=col)
        d.text((X_BODY + 8, ry + 3), lbl, font=fonts["tag"], fill=PABER)

        ty = ry + 32
        for ln in tlines:
            d.text((X_BODY, ty), ln, font=tf, fill=TINT)
            ty += tf.size + 3
        if bands:
            d.text((X_BODY, ty + 2), ellip(d, bands, fonts["bands"], BODY_W),
                   font=fonts["bands"], fill=HALL)
            ty += fonts["bands"].size + 8

        venue = e.get("v", "")
        linn = e.get("linn") or ("" if e.get("c") == "mujal" else e.get("c", ""))
        loc = venue + (", " + linn if linn and linn.lower() not in venue.lower() else "")
        pt = price_text(e)
        ptt = None
        pw = 0
        if pt:
            ptt = ("Pilet: " + pt) if e.get("t") not in ("reliis", "merch") else pt
            ptt = ellip(d, ptt, fonts["price"], int(BODY_W * 0.5))  # hind max pool laiust
            pw = d.textlength(ptt, font=fonts["price"])
        d.text((X_BODY, ty + 2), ellip(d, loc, fonts["venue"], BODY_W - (pw + 24 if pw else 0)),
               font=fonts["venue"], fill=TINT)
        if ptt:
            d.text((X_END - pw, ty + 4), ptt, font=fonts["price"], fill=PAATINA)

        y += rh + gap
        d.line([(MARGIN, int(y) - 11), (W - MARGIN, int(y) - 11)], fill=JOON, width=1)

    if overflow > 0:
        d.text((X_BODY, int(y) + 8), f"+ veel {overflow} üritust — vaata skene.info",
               font=fonts["more"], fill=TELLISKIVI)

    # ---- footer ----
    fy = H - FOOT_H
    d.rectangle([0, fy, W, H], fill=TINT)
    d.text((MARGIN, fy + 28), "skene.info", font=fonts["foot_b"], fill=PABER)
    d.text((MARGIN, fy + 70), "üritused · reliisid · merch", font=fonts["foot_r"], fill=JOON)
    ig = "JÄLGI  @skene.info"
    d.text((W - MARGIN - d.textlength(ig, font=fonts["foot_b"]), fy + 28), ig,
           font=fonts["foot_b"], fill=PABER)
    ir = "Instagram · uus iga nädal"
    d.text((W - MARGIN - d.textlength(ir, font=fonts["foot_r"]), fy + 70), ir,
           font=fonts["foot_r"], fill=JOON)

    img.save(out_path, "JPEG", quality=90)
    return out_path

def page_path(base_out, i):
    """1. leht = base_out; jargmised -2, -3 jne enne laiendit."""
    if i == 1:
        return base_out
    root, ext = os.path.splitext(base_out)
    return f"{root}-{i}{ext}"

def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    ap.add_argument("--data", default=None, help="(vana) uks metal data.json; vaikimisi loeb koik 3 kategooriat repost")
    ap.add_argument("--repo", default=root, help="repo juur (loeb data/, rap/data/, klubi/data/)")
    ap.add_argument("--logo-dir", default=os.path.join(here, "assets", "logo"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--date", default=None)
    ap.add_argument("--from", dest="frm", default=None)
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()

    ref = parse_d(args.date) if args.date else dt.date.today()
    if args.frm:
        ws = parse_d(args.frm)
        we = ws + dt.timedelta(days=args.days - 1)
    else:
        ws, we = this_and_next_week(ref)

    def _load(path, cat, acc):
        if not os.path.exists(path):
            return
        dd = json.load(open(path, encoding="utf-8"))
        for e in dd.get("entries", []):
            if e.get("c") in EESTI and in_window(e, ws, we):
                ee = dict(e); ee["_cat"] = cat; acc.append(ee)
    sel = []
    if args.data:
        _load(args.data, "metal", sel)            # vana kaitumine: uks fail = metal
    else:
        rp = args.repo
        _load(os.path.join(rp, "data", "data.json"), "metal", sel)
        _load(os.path.join(rp, "rap", "data", "data.json"), "rap", sel)
        _load(os.path.join(rp, "klubi", "data", "data.json"), "klubi", sel)
    sel.sort(key=lambda e: (e["d"], CAT_ORDER.index(e.get("_cat", "metal")), e.get("t", "")))

    out = args.out or os.path.join(root, "postitused", f"nadal-{ws.isoformat()}.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if not sel:
        print(f"Aken {ws}..{we}: 0 Eesti kirjet - pilti ei tehtud.")
        return

    fonts = load_fonts()
    d0 = ImageDraw.Draw(Image.new("RGB", (W, H), PABER))  # ainult mootmiseks
    pages = paginate(d0, fonts, sel)

    overflow = 0
    if len(pages) > MAX_PAGES:
        cut = pages[MAX_PAGES:]
        overflow = sum(len(p) for p in cut)
        pages = pages[:MAX_PAGES]
        # viimasele lehele peab "+N veel" rida ara mahtuma
        last = pages[-1]
        while last and START_Y + sum(r[1] for r in last) > ROW_LIMIT - 50:
            overflow += 1
            last.pop()

    logo_path = pick_logo(args.logo_dir)
    n_pages = len(pages)
    paths = []
    for i, rows in enumerate(pages, start=1):
        p = render_page(rows, ws, we, len(sel), i, n_pages, logo_path,
                        page_path(out, i), fonts,
                        overflow=(overflow if i == n_pages else 0))
        paths.append(p)

    shown = sum(len(p_) for p_ in pages)
    print(f"OK: {shown} kirjet {n_pages} pildil"
          + (f", +{overflow} ule aare" if overflow else "")
          + f"; aken {ws}..{we}")
    for p in paths:
        print(f"  {p}")

if __name__ == "__main__":
    main()
