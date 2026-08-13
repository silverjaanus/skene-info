#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genereeri nadal/latest.json (Make.com -> Instagram karussell).

Loeb SAMAD andmed ja kasutab SAMA akna- ning skoobifiltrit nagu
make_weekly_image.py, nii et pildi sisu ja caption ei saa lahku minna.

Enne 28.07.2026 tehti see samm sweepi promptis kasitsi -- ja lainegi lahku:
reliisid kadusid pildilt (linnafilter, vt common.in_scope), aga caption
kirjutati eraldi loogikaga. Nuud tuleb molema sisend uhest kohast.

Kasutus (repo juurest, PARAST make_weekly_image.py-d):
    python scripts/make_weekly_caption.py
    python scripts/make_weekly_caption.py --repo . --date 2026-07-28

Eeldab, et pildid on juba olemas kaustas postitused/ kujul
nadal-<algus>.jpg, nadal-<algus>-2.jpg jne -- skript kopeerib need
avalikku kausta nadal/ ja kirjutab nadal/latest.json.
"""
import argparse
import datetime as dt
import io
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CAT_ORDER, parse_d, this_and_next_week, in_window,
                    today_local, in_scope, is_release, next_start)

BASE_URL = "https://www.skene.info/nadal/"
KUUD = ["jaanuar", "veebruar", "marts", "aprill", "mai", "juuni",
        "juuli", "august", "september", "oktoober", "november", "detsember"]
KUUD_ET = ["jaanuar", "veebruar", "märts", "aprill", "mai", "juuni",
           "juuli", "august", "september", "oktoober", "november", "detsember"]
HASHTAGS = ("#skeneinfo #eestialternatiiv #metal #punk #rock #rap #hiphop "
            "#techno #house #klubi #kontsert #festival #tallinn #tartu")


def load_entries(repo, ws, we):
    srcs = [(os.path.join(repo, "data", "data.json"), "metal"),
            (os.path.join(repo, "rap", "data", "data.json"), "rap"),
            (os.path.join(repo, "klubi", "data", "data.json"), "klubi")]
    out = []
    for path, cat in srcs:
        if not os.path.exists(path):
            continue
        dd = json.load(open(path, encoding="utf-8"))
        for e in dd.get("entries", []):
            if in_scope(e) and in_window(e, ws, we):
                ee = dict(e)
                ee["_cat"] = cat
                out.append(ee)
    for e in out:
        e["_disp"] = next_start(e, ws)
    # sort + kuupaev NAIDATAVA (jargmise) toimumiskuupaeva jargi — sama reegel
    # mis make_weekly_email.py-s ja make_weekly_image.py-s (13.08.2026)
    out.sort(key=lambda e: (e.get("_disp") or e.get("d", ""),
                            CAT_ORDER.index(e.get("_cat", "metal")),
                            e.get("t", "")))
    return out


def line_for(e):
    d = dt.date.fromisoformat(e.get("_disp") or e["d"])
    dm = f"{d.day:02d}.{d.month:02d}"
    if is_release(e):
        silt = "UUS MERCH" if e.get("t") == "merch" else "UUS RELIIS"
        return f"{dm} — {e['n']} · {silt}"
    linn = e.get("linn") or ("" if e.get("c") == "mujal" else e.get("c", ""))
    v = e.get("v", "")
    if v and linn and linn.lower() not in v.lower():
        koht = f"{v}, {linn}"
    else:
        koht = v or linn
    return f"{dm} — {e['n']}" + (f" · {koht}" if koht else "")


CAPTION_LIMIT = 2150  # IG piir on 2200; varu, et Make'i valemi kärbe (backstop)
                      # ei peaks KUNAGI rakenduma — 07.08.2026 kukkus postitus
                      # 2522-margise captioniga, kärbe poole sõna pealt = gibberish


def build_caption(sel, rng):
    """Paneb captioni kokku ja hoiab selle ISE alla IG piiri (13.08.2026):
    kui pikk, asendab viimased uritused reaga '+ veel N uritust' — mitte
    kunagi poolelt sonalt maha loigatud teksti."""
    pea = "TULEVAD ÜRITUSED · " + rng
    saba = ("\n\nKõik üritused ja piletid → skene.info"
            "\nAnna tagasisidet → skene.info/tagasiside"
            "\n\n" + HASHTAGS)
    read = [line_for(e) for e in sel]
    peidetud = 0
    while read:
        body = "\n".join(read)
        if peidetud:
            body += f"\n+ veel {peidetud} üritust → skene.info"
        cap = pea + "\n\n" + body + saba
        if len(cap) <= CAPTION_LIMIT:
            return cap, peidetud
        read.pop()
        peidetud += 1
    return pea + saba, peidetud


def collect_images(repo, ws):
    """Kopeeri postitused/ pildid avalikku nadal/ kausta, tagasta URL-id."""
    src_dir = os.path.join(repo, "postitused")
    dst_dir = os.path.join(repo, "nadal")
    os.makedirs(dst_dir, exist_ok=True)
    urls = []
    i = 1
    while True:
        name = f"nadal-{ws.isoformat()}.jpg" if i == 1 else f"nadal-{ws.isoformat()}-{i}.jpg"
        src = os.path.join(src_dir, name)
        if not os.path.exists(src):
            break
        shutil.copyfile(src, os.path.join(dst_dir, name))
        urls.append(BASE_URL + name)
        i += 1
    return urls


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.dirname(here))
    ap.add_argument("--date", default=None)
    args = ap.parse_args()

    ref = parse_d(args.date) if args.date else today_local()
    ws, we = this_and_next_week(ref)

    sel = load_entries(args.repo, ws, we)
    if not sel:
        print(f"Aken {ws}..{we}: 0 kirjet - latest.json jai puutumata.")
        return

    urls = collect_images(args.repo, ws)
    if not urls:
        print(f"HOIATUS: postitused/nadal-{ws.isoformat()}.jpg puudub - "
              f"jooksuta enne make_weekly_image.py. latest.json jai puutumata.")
        return

    rng = (f"{ws.day}. {KUUD_ET[ws.month - 1]} – "
           f"{we.day}. {KUUD_ET[we.month - 1]} {we.year}")
    caption, peidetud = build_caption(sel, rng)
    if peidetud:
        print(f"MARKUS: caption ulatas {CAPTION_LIMIT} piiri — {peidetud} viimast "
              f"kirjet asendatud reaga '+ veel {peidetud} üritust'.")

    out = {"date": ws.isoformat(),
           "range": rng,
           "image_url": urls[0],       # tagasiuhilduvus (vana Make.com skeem)
           "image_urls": urls,
           "caption": caption}
    path = os.path.join(args.repo, "nadal", "latest.json")
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"OK: {len(sel)} kirjet, {len(urls)} lehte; aken {ws}..{we}")
    print(f"  {path}")


if __name__ == "__main__":
    main()
