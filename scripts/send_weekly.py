#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""send_weekly.py -- kombinatsioonipohine nadalakirja saatmine (bucket-grupid).

Iga tellija pannakse tapselt UHTE 'send:<kombo>:<keel>' ambrisse tema kategooria-
gruppide (metal/rap/klubi) + keele jargi; iga ambri kohta luuakse UKS kampaania
-> iga tellija saab TAPSELT UHE meili, mis sisaldab AINULT tema kategooriaid.

Enne saatmist jookseb ml_sync_groups (grupid signup-valjast). --send ainult Silveri kasul.

Kasutus:
  python scripts/send_weekly.py --repo . --dry-run    # naita ambrid + kirjed, ARA saada
  python scripts/send_weekly.py --repo . --send       # loo + saada kampaaniad
"""
import argparse, json, os, sys, urllib.request, urllib.error, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_weekly_email as gen

API = "https://connect.mailerlite.com/api"

def req(method, path, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header("Authorization", "Bearer " + token)
    r.add_header("Accept", "application/json")
    if data is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            t = resp.read().decode()
            return resp.status, (json.loads(t) if t else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()}

def paged(path, token):
    out, cursor = [], None
    while True:
        p = path + ("&" if "?" in path else "?") + "limit=100"
        if cursor:
            p += "&cursor=" + cursor
        st, b = req("GET", p, token)
        if st >= 300:
            raise SystemExit("GET %s -> %s %s" % (path, st, b))
        out.extend(b.get("data", []))
        cursor = (b.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
    return out

def all_groups(token):
    return {g["name"]: g["id"] for g in paged("/groups", token)}

def ensure_group(name, token, gmap):
    if name in gmap:
        return gmap[name]
    st, b = req("POST", "/groups", token, {"name": name})
    gid = (b.get("data") or {}).get("id")
    gmap[name] = gid
    return gid

def build_subinfo(cat_groups, token):
    """email -> {id, cats:set, lang}. Loeb iga kategooria-grupi tellijad."""
    info = {}
    for cat, gid in cat_groups.items():
        for s in paged("/groups/%s/subscribers?filter[status]=active" % gid, token):
            rec = info.setdefault(s["email"], {"id": s["id"], "cats": set(), "lang": "et"})
            rec["cats"].add(cat)
            lang = (s.get("fields") or {}).get("keel")
            if lang in ("et", "en"):
                rec["lang"] = lang
    return info

def create_campaign(bucket_id, lang, html_content, subject, cfg, token):
    api = cfg.get("api_base", API)
    email = {"subject": subject, "from_name": cfg.get("from_name", "skene.info"),
             "from": cfg["from_email"], "content": html_content}
    payload = {"name": subject, "type": "regular", "emails": [email], "groups": [bucket_id]}
    st, created = req("POST", "/campaigns", token, payload)
    if st >= 300:
        raise RuntimeError("kampaania loomine ebaonnestus: %s %s" % (st, created))
    cid = (created.get("data") or {}).get("id")
    if not cid:
        raise RuntimeError("kampaania ilma id-ta: %s" % created)
    req("POST", "/campaigns/%s/schedule" % cid, token, {"delivery": "instant"})
    return cid

def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--repo", default=os.path.dirname(here))
    ap.add_argument("--config", default="mailerlite_config.json")
    ap.add_argument("--token-file", default="mailerlite_token.txt")
    ap.add_argument("--date", default=None)
    ap.add_argument("--send", action="store_true", help="LOO + saada kampaaniad (muidu dry-run)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    token = open(a.token_file, encoding="utf-8").read().strip()
    gen.MANAGE_LINK = cfg.get("manage_link", gen.MANAGE_LINK)
    cat_groups = cfg["groups"]
    do_send = a.send and not a.dry_run

    ref = gen.parse_d(a.date) if a.date else dt.date.today()
    ws, we = gen.this_and_next_week(ref)
    all_ev = gen.load_sources(a.repo, ws, we)

    subinfo = build_subinfo(cat_groups, token)
    buckets = {}   # name -> {combo, lang, subs:[id]}
    for email, rec in subinfo.items():
        combo = [c for c in gen.CAT_ORDER if c in rec["cats"]]
        if not combo:
            continue
        name = "send:" + "+".join(combo) + ":" + rec["lang"]
        b = buckets.setdefault(name, {"combo": combo, "lang": rec["lang"], "subs": []})
        b["subs"].append(rec["id"])

    print("Aken %s..%s ; %d tellijat, %d ambrit:" % (ws, we, len(subinfo), len(buckets)))
    gmap = all_groups(token)
    send_bucket_ids = {gmap[n] for n in gmap if str(n).startswith("send:")}
    for name, b in sorted(buckets.items()):
        sel = [e for e in all_ev if e.get("_cat") in b["combo"]]
        print("  %-30s %2d tellijat  %2d kirjet" % (name, len(b["subs"]), len(sel)))
        if not do_send:
            continue
        bid = ensure_group(name, token, gmap); send_bucket_ids.add(bid)
        for sid in b["subs"]:
            req("POST", "/subscribers/%s/groups/%s" % (sid, bid), token)
            for oid in send_bucket_ids:
                if oid != bid:
                    req("DELETE", "/subscribers/%s/groups/%s" % (sid, oid), token)
        sel.sort(key=lambda e: (e["d"], gen.CAT_ORDER.index(e.get("_cat", "metal")), e.get("t", "")))
        html = gen.build_html(sel, ws, we, b["lang"], b["combo"])
        rng = gen._plain(gen.daterange(ws, we, gen.I18N[b["lang"]]))
        subj = (cfg.get("subject") or {}).get(b["lang"], "skene.info {range}").replace("{range}", rng)
        cid = create_campaign(bid, b["lang"], html, subj, cfg, token)
        print("     -> SAADETUD kampaania %s" % cid)
    if not do_send:
        print("DRY-RUN: midagi ei saadetud. Paris saatmiseks lisa --send.")

if __name__ == "__main__":
    main()
