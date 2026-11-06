#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fb_kaanepildid.py -- Facebooki ürituste kaanepildid pisipiltideks (Silveri otsus 06.11.2026).

fetch_images.py ei küsi Facebookist midagi (robotid blokitud). Kaanepilt on aga
sageli AINUS pilt, mis üritusel on. Seepärast käib see kahes osas:

  1) python scripts/fb_kaanepildid.py --list [--paevi 21]
     prindib JSON-massiivi tulevastest kirjetest (www/rap/klubi manual.json), millel
     pole `img` ja mille ou/su/pu sisaldab facebook.com/events/<id> linki.

  2) Sweep avab IGA sellise ürituse Silveri sisselogitud brauseris (Chrome), ootab ~3 s
     ja võtab kaanepildi URL-i JavaScriptiga:
        [...document.images].filter(i=>i.naturalWidth>=500&&i.src.includes('fbcdn'))[0]?.src
     ja kontrollib samas, kas pealkiri ütleb "jääb ära"/"canceled"/"tühistatud".
     Tulemused kirjutatakse faili {"<event_id>": "<pildi url>", ...}.

  3) python scripts/fb_kaanepildid.py --apply fail.json
     laeb pildid, salvestab fetch_images.salvesta() kaudu <sait>/pildid/<slug>.webp,
     paneb kirjele img + img_src="fb:<id>". Siis tuleb jooksutada fetch*.py.

fbcdn URL-id aeguvad paari päevaga, seega salvestame pildi kohe oma saidile.
"""
import argparse, datetime as dt, json, re, sys, urllib.request
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_images as fi
from common import slug
from PIL import Image

FB = re.compile(r"facebook\.com/events/(\d+)")


def kirjed():
    for sait in ("www", "rap", "klubi"):
        mfail = fi.SAIDID[sait] / "manual.json"
        raw = json.loads(mfail.read_text(encoding="utf-8"))
        yield sait, mfail, raw, (raw if isinstance(raw, list) else raw["entries"])


def fb_id(e):
    for k in ("ou", "su", "pu"):
        m = FB.search(str(e.get(k) or ""))
        if m:
            return m.group(1)
    return None


def loetle(paevi):
    tana = dt.date.today().isoformat()
    kuni = (dt.date.today() + dt.timedelta(days=paevi)).isoformat()
    out = []
    for sait, _, _, ents in kirjed():
        for e in ents:
            if "img" in e:            # olemas voi teadlik keeld ("")
                continue
            d = str(e.get("dd") or e.get("d") or "")[:10]
            if not (tana <= d <= kuni) and not e.get("rel"):
                continue
            i = fb_id(e)
            if i:
                out.append({"sait": sait, "d": e.get("d"), "n": e.get("n"), "fb": i,
                            "url": f"https://www.facebook.com/events/{i}/"})
    print(json.dumps(out, ensure_ascii=False, indent=1))


def rakenda(fail):
    covers = json.loads(Path(fail).read_text(encoding="utf-8"))
    tehtud = set()
    for sait, mfail, raw, ents in kirjed():
        muutus = 0
        for e in ents:
            if e.get("img"):
                continue
            i = fb_id(e)
            if not i or i not in covers or not covers[i]:
                continue
            try:
                req = urllib.request.Request(covers[i], headers={"User-Agent": "Mozilla/5.0"})
                im = Image.open(BytesIO(urllib.request.urlopen(req, timeout=30).read()))
            except Exception as ex:
                print("!!", sait, e.get("n", "")[:50], type(ex).__name__, ex); continue
            ok, miks = fi.sobib(im, kontrolli_suurust=False)
            if not ok:
                print("--", sait, e.get("n", "")[:50], miks); continue
            s = slug(e.get("n", "")) or slug(str(e.get("d", "")))
            uus = fi.salvesta(im, fi.PILDIKAUST[sait] / (s + ".webp"))
            e["img"] = "pildid/%s.webp" % s
            e["img_src"] = "fb:" + i
            muutus += 1
            tehtud.add(i)
            print("++", sait, e.get("d"), e.get("n", "")[:50], im.size, "->", uus)
        if muutus:
            mfail.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    puudu = [k for k, v in covers.items() if v and k not in tehtud]
    print(f"tehtud {len(tehtud)}/{len(covers)}" + (f", ei leidnud kirjet: {puudu}" if puudu else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--paevi", type=int, default=21)
    ap.add_argument("--apply")
    a = ap.parse_args()
    if a.list:
        loetle(a.paevi)
    elif a.apply:
        rakenda(a.apply)
    else:
        ap.print_help()
