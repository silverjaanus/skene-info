#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_ig_daily.py -- Instagrami paevane sisu (kasvuplaan, etapp 2, 09.10.2026).

Jookseb IGA PAEV Andmekorje lopus (GitHub Actions, ~07:30). Kirjutab alati
ig/today.json; teisipaeval, neljapaeval ja laupaeval teeb lisaks story-pildi
1080x1920 "TANA / HOMME" (Eesti uritused, reliisid ja merch valja).

Make.com loeb https://www.skene.info/ig/today.json ja postitab AINULT siis, kui
  today.json["date"] == tanane kuupaev  JA  today.json["story"]["postita"] == true.
Postitamise luliti on failis data/ig_seaded.json ({"story": false, ...}) --
proovinadalal on see false: pildid tehakse, aga Make ei postita.

Kasutus:
  python scripts/make_ig_daily.py                 # tana
  python scripts/make_ig_daily.py --date 2026-10-13 --force   # test, ka mitte-story paeval
  python scripts/make_ig_daily.py --out-dir C:/temp/ig        # testvaljund mujale
"""
import argparse, datetime as dt, io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import today_local, event_span, in_scope, is_release, CAT_ORDER, order_for_output
import make_weekly_image as mwi
from PIL import Image, ImageDraw

W, H = 1080, 1920
M = 72
STORY_DAYS = {1, 3, 5}          # T, N, L (E=0)
BASE_URL = "https://www.skene.info/ig/"
WDAY = ["E", "T", "K", "N", "R", "L", "P"]
KEEP_DAYS = 14


def happens_on(e, day):
    """Kas uritus toimub antud paeval (tuuri dd-nimekiri voi mitmepaevane vahemik)."""
    if e.get("tba") or is_release(e):
        return False
    dd = e.get("dd")
    if dd:
        return day.isoformat() in dd
    try:
        s, en = event_span(e)
    except Exception:
        return False
    return s <= day <= en


def load_all(repo):
    out = []
    for path, cat in ((os.path.join(repo, "data", "data.json"), "metal"),
                      (os.path.join(repo, "rap", "data", "data.json"), "rap"),
                      (os.path.join(repo, "klubi", "data", "data.json"), "klubi")):
        if not os.path.exists(path):
            continue
        for e in json.load(open(path, encoding="utf-8")).get("entries", []):
            if in_scope(e):
                ee = dict(e); ee["_cat"] = cat; out.append(ee)
    return out


def loc_text(e):
    v = e.get("v", "")
    linn = e.get("linn") or ("" if e.get("c") == "mujal" else e.get("c", ""))
    return v + (", " + linn if linn and linn.lower() not in v.lower() else "")


def render_story(sections, day, out_path, repo):
    """sections = [("TÄNA", date, [entries]), ("HOMME", date, [entries])]"""
    f = mwi.load_fonts()
    big = mwi._display_font(170, 150)
    title = mwi._font(mwi.SANS_B, 44)
    venue = mwi._font(mwi.SANS_R, 32)
    tag = mwi._font(mwi.MONO_B, 22)
    img = Image.new("RGB", (W, H), mwi.TINT)
    d = ImageDraw.Draw(img)
    # IG kate: ulemised ~220 px ja alumised ~260 px katab kasutajaliides -> sisu nende vahel
    logo_path = mwi.pick_logo(os.path.join(repo, "scripts", "assets", "logo"))
    if logo_path:
        lg = Image.open(logo_path).convert("RGBA").resize((96, 96), Image.LANCZOS)
        img.paste(lg, (M, 230), lg)
    gx = M + 96 + 26
    for c in CAT_ORDER:
        d.text((gx, 244), mwi.CAT_WORD[c], font=f["gword"], fill=mwi.CAT_BRIGHT[c])
        gx += d.textlength(mwi.CAT_WORD[c], font=f["gword"]) + 24
    d.text((M + 96 + 26, 322), "SKENE.INFO  ▪  Eesti UG-muusika ühest kohast", font=f["kicker"], fill=mwi.HDRMUTED)

    y = 400
    limit = H - 400
    hidden = 0
    for label, sday, items in sections:
        if not items:
            continue
        if y + 200 > limit:
            hidden += len(items)
            continue
        d.text((M - 6, y), label, font=big, fill=mwi.PABER)
        lw = d.textlength(label, font=big)
        d.text((M + lw + 24, y + 112), f"{WDAY[sday.weekday()]} {sday.day:02d}.{sday.month:02d}",
               font=f["sub"], fill=mwi.CAT_BRIGHT["metal"])
        y += 225
        for i, e in enumerate(items):
            if y + 130 > limit:
                hidden += len(items) - i
                break
            col = mwi.CAT_BRIGHT.get(e.get("_cat"), mwi.HDRMUTED)
            lbl = mwi.CAT_WORD.get(e.get("_cat"), "")
            tw = d.textlength(lbl, font=tag)
            d.rectangle([M, y + 6, M + tw + 18, y + 38], fill=col)
            d.text((M + 9, y + 9), lbl, font=tag, fill=mwi.TINT)
            tx = M + 120   # uhine veerg, et pealkirjad oleksid uhel joonel
            d.text((tx, y), mwi.ellip(d, e.get("n", ""), title, W - M - tx),
                   font=title, fill=mwi.PABER)
            d.text((tx, y + 56), mwi.ellip(d, loc_text(e), venue, W - M - tx),
                   font=venue, fill=mwi.HDRMUTED)
            y += 122
        y += 40
    if hidden:
        d.text((M, min(y, limit + 20)), f"+ veel {hidden} — vaata skene.info", font=f["more"], fill=mwi.CAT_BRIGHT["metal"])
    fy = H - 300
    d.line([(M, fy), (W - M, fy)], fill=mwi.HDRMUTED, width=2)
    d.text((M, fy + 26), "Kõik üritused ja piletid: skene.info", font=f["foot_b"], fill=mwi.PABER)
    d.text((M, fy + 70), "Link profiilis · @skene.info", font=f["foot_r"], fill=mwi.HDRMUTED)
    img.save(out_path, "JPEG", quality=90)
    return out_path


def cleanup(ig_dir, today):
    rx = re.compile(r"^(story|reel|soovitus)-(\d{4}-\d{2}-\d{2}).*\.(jpg|mp4)$")
    for fn in os.listdir(ig_dir):
        m = rx.match(fn)
        if m and dt.date.fromisoformat(m.group(2)) < today - dt.timedelta(days=KEEP_DAYS):
            os.remove(os.path.join(ig_dir, fn))
            print(f"kustutatud: ig/{fn}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.dirname(here))
    ap.add_argument("--date", default=None)
    ap.add_argument("--force", action="store_true", help="tee story ka mitte-story paeval (test)")
    ap.add_argument("--out-dir", default=None, help="testvaljund mujale (today.json-i EI kirjutata)")
    a = ap.parse_args()

    today = dt.date.fromisoformat(a.date) if a.date else today_local()
    tomorrow = today + dt.timedelta(days=1)
    seaded_p = os.path.join(a.repo, "data", "ig_seaded.json")
    seaded = json.load(open(seaded_p, encoding="utf-8")) if os.path.exists(seaded_p) else {}
    ig_dir = a.out_dir or os.path.join(a.repo, "ig")
    os.makedirs(ig_dir, exist_ok=True)

    out = {"date": today.isoformat(), "story": None}
    if today.weekday() in STORY_DAYS or a.force:
        allx = load_all(a.repo)
        t_items = order_for_output([e for e in allx if happens_on(e, today)], today)
        h_items = order_for_output([e for e in allx if happens_on(e, tomorrow)], tomorrow)
        if t_items or h_items:
            name = f"story-{today.isoformat()}.jpg"
            render_story([("TÄNA", today, t_items), ("HOMME", tomorrow, h_items)],
                         today, os.path.join(ig_dir, name), a.repo)
            out["story"] = {"image_url": BASE_URL + name,
                            "tana": len(t_items), "homme": len(h_items),
                            "postita": bool(seaded.get("story", False))}
            print(f"OK story: täna {len(t_items)}, homme {len(h_items)} -> ig/{name}"
                  + ("" if out["story"]["postita"] else "  (postitamine VÄLJAS, data/ig_seaded.json)"))
        else:
            print("Täna ega homme pole Eesti üritusi -- story jääb ära.")
    else:
        print(f"{WDAY[today.weekday()]}: story-päev ei ole.")

    if a.out_dir:
        print(json.dumps(out, ensure_ascii=False))
        return
    cleanup(ig_dir, today)
    with io.open(os.path.join(ig_dir, "today.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    main()
