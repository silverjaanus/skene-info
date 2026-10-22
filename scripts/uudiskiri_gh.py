#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""uudiskiri_gh.py -- reedese uudiskirja automaatne saatmine GitHub Actionsis (22.10.2026).

MIKS: 16.10.2026 blokeeris Claude'i automaatreziimi oiguste kontroll ajastatud
taskis `send_weekly.py --send` kasu ("Real-World Transactions") ja kiri jai 11.45
saatmata. Saatmine kolis seetottu .github/workflows/uudiskiri.yml-i; Claude'i task
`Skene uudiskiri saada` on valja lulitatud. Valvur (Claude'i ajastatud ulesanne R 12:15)
loeb tulemust failist valvur/uudiskiri.json.

Sammud:
  --oota   magab kuni R 11:45 Europe/Tallinn (kui kell on juba ule, jatkab kohe).
           GitHubi cron jaab tunde hiljaks, seega workflow kaivitub vara ja ootab.
  (vaikimisi) eelkontroll -> dry-run -> topeltsaatmise kaitse -> saatmine
  --dry    ainult eelkontroll + dry-run, ei saada

Eelkontroll (sama loogika mis vanas Claude'i taskis):
  (a) nadal/latest.json "date" == tana -> hommikune sweep jooksis
  (b) dry-run: tellijaid > 0 ja uheski ambris pole 0 kirjet
  (c) MailerLite'is pole tanase vahemiku kampaaniat (sent/ready) -> ei saada kaks korda
Tulemus kirjutatakse valvur/uudiskiri.json; viga -> exit 1 (workflow punaseks).
"""
import argparse, datetime as dt, json, os, re, subprocess, sys, time
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_weekly_email as gen   # noqa: E402
import send_weekly as sw          # noqa: E402

try:
    TZ = ZoneInfo("Europe/Tallinn")
except Exception:   # Windowsi Pythonil pole tzdata -- seal on kohalik aeg niikuinii Eesti aeg
    TZ = None
OUT = os.path.join(REPO, "valvur", "uudiskiri.json")


def _nyyd():
    return dt.datetime.now(TZ) if TZ else dt.datetime.now().astimezone()


def kirjuta(seis, **kw):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    d = {"kuupaev": _nyyd().date().isoformat(),
         "aeg": _nyyd().isoformat(timespec="minutes"), "seis": seis}
    d.update(kw)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write("\n")


def katkesta(pohjus, **kw):
    print("UUDISKIRI JAI SAATMATA: " + pohjus)
    kirjuta("saatmata", pohjus=pohjus, **kw)
    sys.exit(1)


def oota():
    nyyd = _nyyd()
    siht = nyyd.replace(hour=11, minute=45, second=0, microsecond=0)
    s = (siht - nyyd).total_seconds()
    if s > 0:
        print(f"Ootan {int(s // 60)} min kuni {siht:%H:%M} (Tallinn)")
        time.sleep(s)
    else:
        print(f"Kell on juba {nyyd:%H:%M} -- jatkan kohe")


def kampaaniad_olemas(token, subjektid):
    leitud = []
    for staatus in ("sent", "ready"):
        st, b = sw.req("GET", f"/campaigns?filter[status]={staatus}&limit=25", token)
        if st >= 300:
            katkesta(f"MailerLite'i kampaaniate paring kukkus ({st}) -- topeltsaatmise kontrolli ei saa teha")
        for c in b.get("data", []):
            if (c.get("name") or "").strip() in subjektid:
                leitud.append(f"{c.get('name')} ({staatus}, {c.get('id')})")
    return leitud


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oota", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if a.oota:
        oota()
        return

    os.chdir(REPO)
    tana = _nyyd().date()

    # (a) sweep
    try:
        latest = json.load(open("nadal/latest.json", encoding="utf-8-sig"))
    except Exception as e:
        katkesta(f"nadal/latest.json ei avane: {e}")
    if latest.get("date") != tana.isoformat():
        if a.dry:   # proovijooks: kontrolli ka MailerLite'i ahelat, kuigi sweep on vana
            print(f"HOIATUS (dry): sweep ei jooksnud tana (latest.json date = {latest.get('date')})")
        else:
            katkesta(f"sweep ei jooksnud tana (nadal/latest.json date = {latest.get('date')})")

    # (b) dry-run
    r = subprocess.run([sys.executable, "scripts/send_weekly.py", "--repo", ".", "--dry-run"],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
        katkesta("send_weekly --dry-run kukkus", viga=r.stderr[-800:])
    ambrid = re.findall(r"^\s+(send:\S+)\s+(\d+) tellijat\s+(\d+) kirjet", r.stdout, re.M)
    tellijaid = sum(int(t) for _, t, _ in ambrid)
    if not ambrid or tellijaid == 0:
        katkesta("dry-run: 0 tellijat voi 0 ambrit", dryrun=r.stdout[-1500:])
    tyhjad = [n for n, _, k in ambrid if int(k) == 0]
    if tyhjad:
        katkesta("tuhi amber: " + ", ".join(tyhjad), dryrun=r.stdout[-1500:])

    # (c) topeltsaatmise kaitse
    cfg = json.load(open("mailerlite_config.json", encoding="utf-8"))
    token = open("mailerlite_token.txt", encoding="utf-8").read().strip()
    ws, we = gen.this_and_next_week(tana)
    subj = set()
    for lang in ("et", "en"):
        rng = gen._plain(gen.daterange(ws, we, gen.I18N[lang]))
        subj.add((cfg.get("subject") or {}).get(lang, "skene.info {range}").replace("{range}", rng))
    olemas = kampaaniad_olemas(token, subj)
    if olemas:
        print("Selle nadala kampaania on juba olemas -- ei saada uuesti: " + "; ".join(olemas))
        kirjuta("juba_saadetud", kampaaniad=olemas)
        return

    ambrite_kokkuvote = [f"{n} {t} tellijat {k} kirjet" for n, t, k in ambrid]
    if a.dry:
        kirjuta("dry_run_ok", ambrid=ambrite_kokkuvote)
        print("DRY: eelkontroll OK, ei saatnud.")
        return

    r = subprocess.run([sys.executable, "scripts/send_weekly.py", "--repo", ".", "--send"],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout)
    saadetud = re.findall(r"SAADETUD kampaania (\S+)", r.stdout)
    if r.returncode != 0 or len(saadetud) != len(ambrid):
        print(r.stderr)
        katkesta(f"saatmine poolik: {len(saadetud)}/{len(ambrid)} ambrit. "
                 "ARA kaivita uuesti tervikuna -- lopeta puuduvad --only send:<kombo>:<keel> --skip-groups",
                 ambrid=ambrite_kokkuvote, kampaaniad=saadetud, logi=(r.stdout + r.stderr)[-1500:])
    kirjuta("saadetud", ambrid=ambrite_kokkuvote, kampaaniad=saadetud, tellijaid=tellijaid)
    print(f"OK: {len(saadetud)} kampaaniat saadetud, {tellijaid} tellijat")


if __name__ == "__main__":
    main()
