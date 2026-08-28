#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dash_push.py -- skene.info dashi (skene.info/dash) sild sweepi/postkastijooksu jaoks.

Kasutus (HANDOVER §2 reegel 18):
  python scripts/dash_push.py                  # PUSH: run-logi + uudiskirja mustand + otsused dashi
  python scripts/dash_push.py --poll           # näita ootel jobid + Silveri vastused (jooksu ALGUSES)
  python scripts/dash_push.py --claim <id>     # võta job enda kanda
  python scripts/dash_push.py --done <id> --note "kokkuvõte"   # märgi job valmis

Saladus: repo juurkausta .env failist rida DASH_SECRET=... (või env-muutuja DASH_SECRET).
API: https://www.skene.info/api/dash (vt api/dash.js ja PROJEKT.md 5D).
Otsustuspunktid: kui on olemas sweep/otsused.json (massiiv objektidest
{oid, kysimus, kontekst, valikud:[{id,tekst}], lingid:[], vaikeotsus, tahtaeg}),
pushitakse see dashi "Otsust ootab" plokki. Tühi massiiv = plokk tühjeneb.
"""
import argparse, glob, json, os, re, sys, urllib.parse, urllib.request

JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.environ.get("DASH_API", "https://www.skene.info/api/dash")


def loe_secret():
    s = os.environ.get("DASH_SECRET", "")
    if s:
        return s
    env_fail = os.path.join(JUUR, ".env")
    if os.path.exists(env_fail):
        with open(env_fail, encoding="utf-8") as f:
            for rida in f:
                m = re.match(r"\s*DASH_SECRET\s*=\s*(.+?)\s*$", rida)
                if m:
                    return m.group(1).strip('"\'')
    sys.exit("DASH_SECRET puudub (.env rida DASH_SECRET=... või env-muutuja).")


def api(secret, method="GET", params="", body=None):
    url = API + "?t=" + urllib.parse.quote(secret) + ("&" + params if params else "")
    data = None
    if body is not None:
        body = dict(body)
        body["t"] = secret
        data = json.dumps(body).encode("utf-8")
        url = API
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def viimane_runlog():
    failid = sorted(glob.glob(os.path.join(JUUR, "sweep", "run-*.json")))
    if not failid:
        return None
    with open(failid[-1], encoding="utf-8") as f:
        d = json.load(f)
    uusi = d.get("uusi") or {}
    if isinstance(uusi, dict):
        uusi_kokku = sum(v for v in uusi.values() if isinstance(v, int))
    else:
        uusi_kokku = uusi
    return {
        "kuupaev": d.get("kuupaev"),
        "allikaid": d.get("allikaid"),
        "avatud": d.get("avatud"),
        "skipitud": len(d.get("skipitud") or []),
        "uusi": uusi_kokku,
        "uusi_jaotus": uusi if isinstance(uusi, dict) else {},
        "markus": (d.get("markus") or "")[:400],
    }


def uudiskirja_mustandid():
    """Värskeim postitused/*.et.html + sama nimega .en.html (make_weekly_email.py väljund)."""
    et_failid = sorted(glob.glob(os.path.join(JUUR, "postitused", "*.et.html")),
                       key=os.path.getmtime)
    if not et_failid:
        return None, None
    et_fail = et_failid[-1]
    en_fail = et_fail[:-8] + ".en.html"

    def loe(p):
        if p and os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return f.read()
        return None
    return loe(et_fail), loe(en_fail)


def push(secret):
    run = viimane_runlog()
    if run:
        r = api(secret, "POST", body={"action": "set_seis", "seis": {"run": run}})
        print("set_seis:", r.get("ok"), run["kuupaev"])
    et, en = uudiskirja_mustandid()
    if et or en:
        r = api(secret, "POST", body={"action": "set_uudiskiri", "et": et, "en": en})
        print("set_uudiskiri:", r.get("ok"), "et" if et else "", "en" if en else "")
    otsused_fail = os.path.join(JUUR, "sweep", "otsused.json")
    if os.path.exists(otsused_fail):
        with open(otsused_fail, encoding="utf-8") as f:
            otsused = json.load(f)
        r = api(secret, "POST", body={"action": "set_otsused", "otsused": otsused})
        print("set_otsused:", r.get("ok"), len(otsused), "tk")
    print("PUSH OK")


def poll(secret):
    d = api(secret, params="mode=poll")
    if not d.get("ok"):
        sys.exit("Polli viga: " + str(d.get("error")))
    print("KAIMAS:", json.dumps(d.get("kaimas"), ensure_ascii=False))
    print("QUEUE (%d):" % len(d.get("queue") or []))
    for j in d.get("queue") or []:
        print("  id=%s  tyyp=%s  full=%s  markus=%r  loodud=%s" %
              (j["id"], j["tyyp"], j.get("full", 0), j.get("markus", ""), j.get("loodud")))
    print("TOOTLEMATA VASTUSED (%d):" % len(d.get("vastused") or []))
    for v in d.get("vastused") or []:
        print("  oid=%s  valik=%s  markus=%r  (märgi rakendatuks: POST vastus_toodeldud)" %
              (v["oid"], v["valik"], v.get("markus", "")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--poll", action="store_true")
    ap.add_argument("--claim", metavar="ID")
    ap.add_argument("--done", metavar="ID")
    ap.add_argument("--note", default="")
    ap.add_argument("--vastus-toodeldud", metavar="OID")
    a = ap.parse_args()
    s = loe_secret()
    if a.poll:
        poll(s)
    elif a.claim:
        print(json.dumps(api(s, "POST", body={"action": "vota_job", "id": a.claim}),
                         ensure_ascii=False))
    elif a.done:
        print(json.dumps(api(s, "POST", body={"action": "job_valmis", "id": a.done,
                                              "note": a.note}), ensure_ascii=False))
    elif a.vastus_toodeldud:
        print(json.dumps(api(s, "POST", body={"action": "vastus_toodeldud",
                                              "oid": a.vastus_toodeldud}), ensure_ascii=False))
    else:
        push(s)


if __name__ == "__main__":
    main()
