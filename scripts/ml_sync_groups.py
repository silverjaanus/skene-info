#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ml_sync_groups.py -- sunkroonib tellijate 'grupid'-valja MailerLite gruppidega.

Loeb aktiivsed tellijad, kellel 'grupid' valja on taidetud (nt "metal,rap"),
maarab need grupid (lisab puuduvad, eemaldab liigsed AINULT 3 kategooria-grupi seast),
seejarel TUHJENDAB 'grupid'-valja -- see on uhekordne signup-uleandmine; edasine
gruppide haldus kaib MailerLite eelistuste-lehel.

Kasutus:
  python scripts/ml_sync_groups.py [--config mailerlite_config.json]
      [--token-file mailerlite_token.txt] [--dry-run]
"""
import argparse, json, urllib.request, urllib.error

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

def list_active(token):
    subs, cursor = [], None
    while True:
        path = "/subscribers?limit=100&filter[status]=active"
        if cursor:
            path += "&cursor=" + cursor
        st, body = req("GET", path, token)
        if st >= 300:
            raise SystemExit("LIST ERR %s %s" % (st, body))
        subs.extend(body.get("data", []))
        cursor = (body.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
    return subs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="mailerlite_config.json")
    ap.add_argument("--token-file", default="mailerlite_token.txt")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    token = open(a.token_file, encoding="utf-8").read().strip()
    groups = cfg["groups"]                       # name -> id
    cats = set(groups.keys())
    name_by_id = {v: k for k, v in groups.items()}

    subs = list_active(token)
    changed = 0
    for s in subs:
        gid = (s.get("fields") or {}).get("grupid")
        if not gid:
            continue
        # signup LISAB ainult kategooriaid (eemaldamine kaib ML eelistuste-lehel)
        desired = [c.strip() for c in str(gid).split(",") if c.strip() in cats]
        sid = s["id"]; email = s.get("email")
        print("%s: field=[%s] -> lisan grupid %s" % (email, gid, desired))
        if a.dry_run:
            changed += 1; continue
        for c in desired:
            req("POST", "/subscribers/%s/groups/%s" % (sid, groups[c]), token)
        # tuhjenda 'grupid' vali (upsert e-posti jargi)
        req("POST", "/subscribers", token, {"email": email, "fields": {"grupid": ""}})
        changed += 1
    print("Synced %d subscriber(s)." % changed)

if __name__ == "__main__":
    main()
