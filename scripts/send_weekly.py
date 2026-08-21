#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""send_weekly.py -- kombinatsioonipohine nadalakirja saatmine (bucket-grupid).

Iga tellija pannakse tapselt UHTE 'send:<kombo>:<keel>' ambrisse tema kategooria-
gruppide (metal/rap/klubi) + keele jargi; iga ambri kohta luuakse UKS kampaania
-> iga tellija saab TAPSELT UHE meili, mis sisaldab AINULT tema kategooriaid.

NB (muudetud 21.08.2026 audit): --send kaivitab EELSAMMUD nuud ISE ja katkestab
nende vea korral: (1) check_send_parity.py -- jarjestus saatmistees == eelvaade
(14.08 intsident: reegel oli kirjas, aga jai kaivitamata ja vale kiri laks valja);
(2) ml_sync_groups.py -- uute tellijate signup-grupid ambritesse (oli varem
kasitsi-kohustus, mida sai unustada). Ainult hadaolukorras: --skip-gates.
--send ainult Silveri kasul.

Kasutus:
  python scripts/send_weekly.py --repo . --dry-run    # naita ambrid + kirjed, ARA saada
  python scripts/send_weekly.py --repo . --send       # loo + saada kampaaniad
"""
import argparse, json, os, subprocess, sys, time, urllib.request, urllib.error, datetime as dt
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
    except urllib.error.URLError as e:
        print("VORGUVIGA %s %s: %s" % (method, path, e.reason))
        return 599, {"error": str(e.reason)}

def req_ok(method, path, token, body=None, tries=5):
    """Nagu req(), aga KONTROLLIB tulemust: 429 (rate limit) -> ootab ja proovib uuesti,
    muu viga -> RuntimeError. 02.08.2026: liikmelisuse tsukkel ignoreeris req() staatust,
    mistottu uks 429-ga ebaonnestunud POST jattis tellija vaikselt ambrist valja."""
    for i in range(tries):
        st, b = req(method, path, token, body)
        if 200 <= st < 300:
            return st, b
        if st in (429, 599):
            wait = 20 * (i + 1)
            print("     %s %s -> %s, ootan %d s (katse %d/%d)" % (method, path, st, wait, i + 1, tries))
            time.sleep(wait)
            continue
        raise RuntimeError("%s %s -> %s %s" % (method, path, st, b))
    raise RuntimeError("%s %s: rate limit ei taandunud %d katsega" % (method, path, tries))

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
    if not (200 <= st < 300) or not gid:
        raise RuntimeError("grupi '%s' loomine ebaonnestus (%s): %s" % (name, st, b))
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

def gate(cmd, mis):
    """Kohustuslik eelsamm --send'ile: jooksuta alamprotsessina, vea korral
    KATKESTA saatmine. 21.08.2026 audit: varem olid need dokumenteeritud
    kasitsi-kohustused (HANDOVER/PROJEKT.md), mida sai unustada -- 14.08 laks
    kiri valja ilma parity-kontrollita ja jarjestus oli vale."""
    print("EELSAMM: %s" % mis)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit("VIGA: eelsamm '%s' kukkus (exit %d) -- SAATMINE KATKESTATUD. "
                         "Paranda pohjus voi (ainult hadaolukorras) kasuta --skip-gates."
                         % (mis, r.returncode))


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--repo", default=os.path.dirname(here))
    ap.add_argument("--config", default="mailerlite_config.json")
    ap.add_argument("--token-file", default="mailerlite_token.txt")
    ap.add_argument("--date", default=None)
    ap.add_argument("--send", action="store_true", help="LOO + saada kampaaniad (muidu dry-run)")
    ap.add_argument("--dry-run", action="store_true")
    # Taastamine poolelijaanud saatmisest (nt MailerLite 429 rate limit keset jooksu):
    # --only saadab AINULT nimetatud ambri, --skip-groups jatab liikmelisuse sunki vahele,
    # kui see ambri jaoks juba onnestus (POST/DELETE tsukkel joudis labi, kampaania mitte).
    ap.add_argument("--only", default=None, help="ainult see amber, nt send:metal:et")
    ap.add_argument("--skip-groups", action="store_true", help="ara muuda ambri liikmelisust")
    ap.add_argument("--settle", type=int, default=30,
                    help="sekundeid liikmelisuse ja kampaania loomise vahel (vaikimisi 30)")
    ap.add_argument("--no-intro", action="store_true",
                    help="jata data/uudiskiri-intro.json plokk kirjast valja")
    ap.add_argument("--skip-gates", action="store_true",
                    help="HADAOLUKORRAKS: jata --send eelsammud (parity + group-sync) vahele")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    token = open(a.token_file, encoding="utf-8").read().strip()
    gen.MANAGE_LINK = cfg.get("manage_link", gen.MANAGE_LINK)
    cat_groups = cfg["groups"]
    do_send = a.send and not a.dry_run

    # Kohustuslikud eelsammud enne parissaatmist (vt gate() ja mooduli docstring).
    if do_send and not a.skip_gates:
        gate([sys.executable, os.path.join(here, "check_send_parity.py"),
              "--repo", a.repo],
             "check_send_parity (jarjestus saatmistees == eelvaade)")
        gate([sys.executable, os.path.join(here, "ml_sync_groups.py"),
              "--config", a.config, "--token-file", a.token_file],
             "ml_sync_groups (uute tellijate grupid signup-valjast)")
    elif do_send and a.skip_gates:
        print("HOIATUS: --skip-gates — parity- ja group-sync eelsammud JAETI VAHELE.")

    ref = gen.parse_d(a.date) if a.date else dt.date.today()
    ws, we = gen.this_and_next_week(ref)
    # Sissejuhatav plokk (data/uudiskiri-intro.json). Aegub ise -- vt gen.load_intro().
    if not a.no_intro:
        gen.load_intro(a.repo, ref)
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
        # ⚠ JARJESTUS: ainus allikas on common.order_for_output(), sama funktsioon,
        # mida kutsub make_weekly_email.gen_combo(). 14.08.2026 oli siin OMA koopia
        # sortimisest (`e["d"]` + CAT_ORDER), mis ei kasutanud _disp'i ega
        # interleave'i -- eelvaade oli oige, valjalainud kiri vale. Ara too koopiat tagasi.
        sel = gen.order_for_output(sel, ws)
        # HTML ehitatakse ALATI, ka dry-run'is: nii katab eelkontroll ka renderdustee
        # (varem ehitati HTML alles parast `continue`-t ja dry-run ei naidanud sisu).
        html = gen.build_html(sel, ws, we, b["lang"], b["combo"])
        skip = a.only and name != a.only
        esimene = (sel[0].get("_disp") or sel[0].get("d", "?")) if sel else "-"
        print("  %-30s %2d tellijat  %2d kirjet  (1. kirje %s)%s" % (
            name, len(b["subs"]), len(sel), esimene,
            "  [VAHELE JAETUD --only]" if skip else ""))
        if skip or not do_send:
            continue
        bid = ensure_group(name, token, gmap); send_bucket_ids.add(bid)
        if not a.skip_groups:
            for sid in b["subs"]:
                req_ok("POST", "/subscribers/%s/groups/%s" % (sid, bid), token)
                for oid in send_bucket_ids:
                    if oid != bid:
                        req_ok("DELETE", "/subscribers/%s/groups/%s" % (sid, oid), token)
            # MailerLite votab kampaania saajate nimekirja hetkeseisuga: varskelt lisatud
            # liikmed ei pruugi kohe kohal olla (02.08.2026 laks uks kampaania 0 saajale).
            time.sleep(a.settle)
        rng = gen._plain(gen.daterange(ws, we, gen.I18N[b["lang"]]))
        subj = (cfg.get("subject") or {}).get(b["lang"], "skene.info {range}").replace("{range}", rng)
        cid = create_campaign(bid, b["lang"], html, subj, cfg, token)
        print("     -> SAADETUD kampaania %s" % cid)
    if not do_send:
        print("DRY-RUN: midagi ei saadetud. Paris saatmiseks lisa --send.")

if __name__ == "__main__":
    main()
