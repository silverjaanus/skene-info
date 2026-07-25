#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ml_sync_groups.py -- sunkroonib tellijate 'grupid'-valja MailerLite gruppidega
ja hoiab eelistuste-lehe HMAC-tokenit kliendivaljal.

1) SIGNUP-ULEANDMINE: tellijad, kellel 'grupid' vali on taidetud (nt "metal,rap"),
   saavad need grupid juurde (LISAB, ei eemalda -- eemaldamine kaib eelistuste-lehel),
   seejarel tuhjendatakse 'grupid' vali.
2) TOKEN: igale aktiivsele tellijale arvutatakse tok = HMAC-SHA256(saladus, email)[:16]
   ja kirjutatakse kliendivaljale (cfg["field_token"], vaikimisi "tok"). Kirjas olev link
   ?e={$email}&t={$tok} viib lehele /eelistused.html, mille api/eelistused.js kontrollib
   sama arvutusega. Saladus PEAB olema sama, mis Verceli env-muutuja PREF_SECRET.

MailerLite tasuta plaanil eelistuste-keskust EI OLE (403), seetottu oma leht.

Kasutus:
  python scripts/ml_sync_groups.py [--config mailerlite_config.json]
      [--token-file mailerlite_token.txt] [--secret-file mailerlite_pref_token.txt]
      [--dry-run] [--init-secret] [--skip-tokens]
"""
import argparse, hashlib, hmac, json, os, secrets, urllib.request, urllib.error

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

def tok_for(secret, email):
    return hmac.new(secret.encode(), email.strip().lower().encode(),
                    hashlib.sha256).hexdigest()[:16]

def load_secret(path, init):
    if os.path.exists(path):
        s = open(path, encoding="utf-8").read().strip()
        if s:
            return s
    if not init:
        raise SystemExit(
            "Saladuse fail puudub voi tuhi: %s\n"
            "Loo see --init-secret lipuga ja pane SAMA vaartus Verceli "
            "env-muutujaks PREF_SECRET." % path)
    s = secrets.token_hex(32)
    with open(path, "w", encoding="utf-8") as f:
        f.write(s + "\n")
    print("Uus saladus kirjutatud faili %s" % path)
    print("PANE SEE Verceli env-muutujaks PREF_SECRET:\n%s" % s)
    return s

def ensure_field(token, key, dry):
    """Tagastab olemasoleva kliendivalja key voi loob selle."""
    st, body = req("GET", "/fields?limit=100", token)
    if st >= 300:
        raise SystemExit("FIELDS ERR %s %s" % (st, body))
    for f in body.get("data", []):
        if f.get("key") == key or f.get("name") == key:
            return f.get("key")
    if dry:
        print("[dry-run] looks kliendivalja '%s'" % key)
        return key
    st, body = req("POST", "/fields", token, {"name": key, "type": "text"})
    if st >= 300:
        raise SystemExit("FIELD CREATE ERR %s %s" % (st, body))
    newkey = ((body.get("data") or {}).get("key")) or key
    print("Loodud kliendivali '%s' (merge-tag {$%s})" % (newkey, newkey))
    return newkey

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="mailerlite_config.json")
    ap.add_argument("--token-file", default="mailerlite_token.txt")
    ap.add_argument("--secret-file", default="mailerlite_pref_token.txt")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--init-secret", action="store_true",
                    help="loo saladuse fail kui puudub (prindib PREF_SECRET vaartuse)")
    ap.add_argument("--skip-tokens", action="store_true",
                    help="ara puutu eelistuste-lehe tokeneid")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    token = open(a.token_file, encoding="utf-8").read().strip()
    groups = cfg["groups"]                       # name -> id
    cats = set(groups.keys())

    fkey, secret = None, None
    if not a.skip_tokens:
        secret = load_secret(a.secret_file, a.init_secret)
        fkey = ensure_field(token, cfg.get("field_token", "tok"), a.dry_run)
        if fkey != cfg.get("field_token"):
            print("MARKUS: pane mailerlite_config.json \"field_token\": \"%s\" "
                  "ja manage_link ...&t={$%s}" % (fkey, fkey))

    subs = list_active(token)
    changed = 0
    for s in subs:
        sid = s["id"]; email = s.get("email") or ""
        fields = s.get("fields") or {}
        upd = {}
        gid = fields.get("grupid")
        desired = []
        if gid:
            # signup LISAB ainult kategooriaid (eemaldamine kaib /eelistused.html-il)
            desired = [c.strip() for c in str(gid).split(",") if c.strip() in cats]
            upd["grupid"] = ""
        if fkey and secret:
            want = tok_for(secret, email)
            if (fields.get(fkey) or "") != want:
                upd[fkey] = want
        if not desired and not upd:
            continue
        print("%s: grupid=[%s] -> %s | valjad %s"
              % (email, gid or "", desired or "-", sorted(upd.keys())))
        if a.dry_run:
            changed += 1; continue
        for c in desired:
            req("POST", "/subscribers/%s/groups/%s" % (sid, groups[c]), token)
        if upd:
            req("POST", "/subscribers", token, {"email": email, "fields": upd})
        changed += 1
    print("Synced %d subscriber(s)." % changed)

if __name__ == "__main__":
    main()
