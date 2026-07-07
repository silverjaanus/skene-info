#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_weekly_image.py -- genereerib skene.info nadalapildi (metal-pool).

Loeb data/data.json, filtreerib tuleva E-P nadala Eesti uritused + reliisid,
renderdab 1080x1350 JPG saidi varvipaletiga, logo nurgas juhuslikus variandis.

Kasutus:
  python scripts/make_weekly_image.py                      # tulev E-P nadal
  python scripts/make_weekly_image.py --date 2026-07-13    # ref-kuupaev (test)
  python scripts/make_weekly_image.py --from 2026-07-13 --days 7
  python scripts/make_weekly_image.py --data data/data.json --out postitused/x.jpg

Reeglid (vt PROJEKT.md):
  - Ainult Eesti: c in {Tallinn, Tartu, mujal}. Rahvusvahelised jaavad valja.
  - Hinda EI leiutata: kui 'hind' puudub, jaetakse hinnarida ara.
  - Mahupiir: kuni MAX_ROWS kirjet; ulejaak -> "+N veel skene.info-s".
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
KUUD_GEN = {1:"jaanuar",2:"veebruar",3:"marts",4:"aprill",5:"mai",6:"juuni",
            7:"juuli",8:"august",9:"september",10:"oktoober",11:"november",12:"detsember"}

W, H = 1080, 1350
MARGIN = 64
MAX_ROWS = 7

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
    for sep in [";", " \u2014 ", " - ", " / ", ",", " ("]:
        if sep in p:
            p = p.split(sep)[0].strip()
    if not p:
        return None
    if h.get("kuni") and h.get("jargmine"):
        return f"{p} \u2192 {h['jargmine']}"
    return p

def render(entries, ws, we, logo_dir, out_path):
    fonts = load_fonts()
    img = Image.new("RGB", (W, H), PABER)
    d = ImageDraw.Draw(img)

    x_date = MARGIN
    x_body = MARGIN + 148
    x_end = W - MARGIN
    body_w = x_end - x_body

    # ---- pais ----
    d.text((MARGIN, 48), "SKENE.INFO  ·  EESTI ALTERNATIIV", font=fonts["eyebrow"], fill=HALL)
    d.text((MARGIN, 82), "TULEVAD", font=fonts["h1"], fill=TINT)
    d.text((MARGIN, 82 + 84), "ÜRITUSED", font=fonts["h1"], fill=TINT)
    if ws.month == we.month:
        rng = f"{ws.day}.–{we.day}. {KUUD_GEN[ws.month]} {we.year}"
    else:
        rng = f"{ws.day}. {KUUD_GEN[ws.month]} – {we.day}. {KUUD_GEN[we.month]} {we.year}"
    n = len(entries)
    sub = f"{rng}  ·  {n} kirje" + ("" if n == 1 else "t")
    sub_y = 82 + 84 + 88
    d.text((MARGIN, sub_y), sub, font=fonts["sub"], fill=TELLISKIVI)

    # ---- logo nurka (juhuslik variant) ----
    variants = ["v1", "v2", "v5", "v8", "v9", "v10"]
    random.shuffle(variants)
    for v in variants:
        p = os.path.join(logo_dir, f"{v}.png")
        if os.path.exists(p):
            logo = Image.open(p).convert("RGBA").resize((128, 128), Image.LANCZOS)
            img.paste(logo, (W - MARGIN - 128, 52), logo)
            break

    top = sub_y + 46
    d.line([(MARGIN, top), (W - MARGIN, top)], fill=TINT, width=3)

    # ---- reakorguse mootmine ----
    def measure(e):
        tf = fonts["title"] if len(e.get("n", "")) < 40 else fonts["title_s"]
        tlines = wrap(d, e.get("n", ""), tf, body_w, 2)
        bands = " · ".join(e.get("b", [])) if e.get("b") else e.get("a", "")
        h = 30 + len(tlines) * (tf.size + 3)
        if bands:
            h += fonts["bands"].size + 8
        h += fonts["venue"].size + 6
        return max(h, 70) + 16, tf, tlines, bands

    foot_h = 120
    row_limit = (H - foot_h) - 16
    start_y = top + 8

    # vali mahtuvad read (jata overflow-reale ruumi)
    picks = []
    used = 0
    for i, e in enumerate(entries):
        rh, tf, tlines, bands = measure(e)
        remaining = len(entries) - i
        reserve = 40 if remaining > 1 else 0
        if len(picks) >= MAX_ROWS or start_y + used + rh > row_limit - reserve:
            break
        picks.append([e, rh, tf, tlines, bands])
        used += rh
    overflow = len(entries) - len(picks)

    # jaota vaba ruum ridade vahele (tasakaal, kui pole overflow'i)
    slack = row_limit - (start_y + used)
    gap = 0
    if overflow == 0 and len(picks) > 0 and slack > 0:
        gap = min(slack / len(picks), 46)

    WDAY = ["E", "T", "K", "N", "R", "L", "P"]
    y = start_y
    for e, rh, tf, tlines, bands in picks:
        ry = int(y + gap * 0.35)
        s, en = event_span(e)
        col = TYPE_COLOR.get(e.get("t"), HALL)

        d.text((x_date, ry + 2), f"{s.day:02d}.{s.month:02d}", font=fonts["date"], fill=TINT)
        if e.get("t") in ("reliis", "merch") or e.get("rel"):
            d.text((x_date, ry + 44), e.get("t", "reliis"), font=fonts["wday"], fill=col)
        else:
            wl = WDAY[s.weekday()]
            if e.get("d2"):
                wl += f" – {en.day:02d}.{en.month:02d}"
            d.text((x_date, ry + 44), wl, font=fonts["wday"], fill=HALL)

        lbl = TYPE_LABEL.get(e.get("t"), e.get("t", "").upper())
        tw2 = d.textlength(lbl, font=fonts["tag"])
        d.rectangle([x_body, ry, x_body + tw2 + 16, ry + 25], fill=col)
        d.text((x_body + 8, ry + 3), lbl, font=fonts["tag"],
               fill=(PABER if col != SINEP else TINT))

        ty = ry + 32
        for ln in tlines:
            d.text((x_body, ty), ln, font=tf, fill=TINT)
            ty += tf.size + 3
        if bands:
            d.text((x_body, ty + 2), ellip(d, bands, fonts["bands"], body_w),
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
            ptt = ellip(d, ptt, fonts["price"], int(body_w * 0.5))  # hind max pool laiust
            pw = d.textlength(ptt, font=fonts["price"])
        d.text((x_body, ty + 2), ellip(d, loc, fonts["venue"], body_w - (pw + 24 if pw else 0)),
               font=fonts["venue"], fill=TINT)
        if ptt:
            d.text((x_end - pw, ty + 4), ptt, font=fonts["price"], fill=PAATINA)

        y += rh + gap
        d.line([(MARGIN, int(y) - 11), (W - MARGIN, int(y) - 11)], fill=JOON, width=1)

    if overflow > 0:
        d.text((x_body, int(y) + 8), f"+ veel {overflow} üritust — vaata skene.info",
               font=fonts["more"], fill=TELLISKIVI)

    # ---- footer ----
    fy = H - foot_h
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
    return out_path, len(picks), overflow

def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    ap.add_argument("--data", default=os.path.join(root, "data", "data.json"))
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

    with open(args.data, encoding="utf-8") as f:
        data = json.load(f)
    entries = data.get("entries", [])
    sel = [e for e in entries if e.get("c") in EESTI and in_window(e, ws, we)]
    sel.sort(key=lambda e: (e["d"], e.get("t", "")))

    out = args.out or os.path.join(root, "postitused", f"nadal-{ws.isoformat()}.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if not sel:
        print(f"Aken {ws}..{we}: 0 Eesti kirjet - pilti ei tehtud.")
        return
    path, shown, overflow = render(sel, ws, we, args.logo_dir, out)
    print(f"OK: {path}  ({shown} pildil" + (f", +{overflow} ule aare" if overflow else "")
          + f"; aken {ws}..{we})")

if __name__ == "__main__":
    main()
