#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ig_publish.py -- postitab tanase Instagrami story (kasvuplaan, etapp 2, 09.10.2026).

Postitab otse Instagrami API-ga (Instagram Login), oma Meta app
"skene.info postitaja" (2331682427587673). Jookseb GitHub Actionsis
(.github/workflows/ig_story.yml).

Postitab AINULT siis, kui:
  - ig/today.json["date"] == tana (Europe/Tallinn)
  - ig/today.json["story"]["postita"] == true  (luliti: data/ig_seaded.json)
  - tanast storyt pole veel postitatud (ig/postitatud.json)
  - keskkonnas on IG_TOKEN (GitHubi secret, seda EI hoita repos)

Token kehtib 60 paeva; iga jooks pikendab seda (refresh_access_token) ja
workflow salvestab uue tokeni tagasi secret'isse (vajab secret'it GH_PAT).

Kasutus:  python scripts/ig_publish.py [--dry-run] [--check]
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import today_local

IG_USER_ID = "17841409504581888"     # @skene.info
GRAPH = "https://graph.instagram.com"
VER = "v23.0"


def call(method, path, params):
    data = urllib.parse.urlencode(params)
    if method == "GET":
        req = urllib.request.Request(f"{GRAPH}/{path}?{data}")
    else:
        req = urllib.request.Request(f"{GRAPH}/{path}", data=data.encode(), method="POST")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        sys.exit(f"VIGA {e.code} {path}: {body[:500]}")


def refresh(token):
    """Pikenda tokenit (lubatud, kui token on >24 h vana). Viga siin ei peata postitamist."""
    try:
        r = urllib.request.urlopen(f"{GRAPH}/refresh_access_token?grant_type=ig_refresh_token&access_token="
                                   + urllib.parse.quote(token), timeout=30)
        d = json.loads(r.read())
        paevi = int(d.get("expires_in", 0)) // 86400
        uus = d.get("access_token")
        muutus = uus not in (None, token)
        print(f"Token pikendatud: kehtib {paevi} paeva" + (" (uus token)" if muutus else ""))
        # workflow salvestab uue tokeni secret'isse (gh secret set, GH_PAT)
        out = os.environ.get("IG_NEW_TOKEN_FILE")
        if muutus and out:
            print(f"::add-mask::{uus}")
            with open(out, "w") as f:
                f.write(uus)
    except urllib.error.HTTPError as e:
        print(f"Tokeni pikendus ei onnestunud ({e.code}): {e.read().decode('utf-8', 'replace')[:200]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="ainult kontrolli, kas token tootab")
    a = ap.parse_args()

    token = os.environ.get("IG_TOKEN", "").strip()
    if not token:
        print("IG_TOKEN puudub (GitHubi secret seadistamata) -- ei postita."); return
    if a.check:
        me = call("GET", f"{VER}/me", {"fields": "user_id,username", "access_token": token})
        print(f"Token OK: @{me.get('username')} ({me.get('user_id')})")
        refresh(token)   # kontrollib ka uuenduse + salvestamise ahelat
        return
    if not a.dry_run:
        refresh(token)

    today = today_local().isoformat()
    tj = json.load(open(os.path.join(a.repo, "ig", "today.json"), encoding="utf-8"))
    st = tj.get("story")
    if tj.get("date") != today:
        print(f"today.json on {tj.get('date')}, mitte {today} -- korje ei jooksnud? Ei postita."); return
    if not st:
        print("Täna story't pole."); return
    if not st.get("postita"):
        print("Postitamine on välja lülitatud (data/ig_seaded.json)."); return

    logp = os.path.join(a.repo, "ig", "postitatud.json")
    log = json.load(open(logp, encoding="utf-8")) if os.path.exists(logp) else {}
    if today in log:
        print(f"Tänane story juba postitatud: {log[today]}"); return
    if a.dry_run:
        print(f"DRY-RUN: postitaksin {st['image_url']}"); return

    c = call("POST", f"{VER}/{IG_USER_ID}/media",
             {"image_url": st["image_url"], "media_type": "STORIES", "access_token": token})
    cid = c["id"]
    for _ in range(30):
        s = call("GET", f"{VER}/{cid}", {"fields": "status_code", "access_token": token})
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            sys.exit(f"VIGA: meedia töötlus {s}")
        time.sleep(5)
    p = call("POST", f"{VER}/{IG_USER_ID}/media_publish", {"creation_id": cid, "access_token": token})

    log[today] = {"media_id": p.get("id"), "image_url": st["image_url"]}
    keep = sorted(log)[-30:]
    log = {k: log[k] for k in keep}
    with open(logp, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"OK: story postitatud (media {p.get('id')})")
    telegram_pilt(st["image_url"])


def telegram_pilt(url):
    """Saada Silverile originaalpilt Telegrami, et ta saaks selle oma kontol täies kvaliteedis jagada."""
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not tok:
        return
    cap = ("📸 skene.info story on üleval. Tahad oma kontol jagada? Salvesta see pilt ja lisa lingikleeps: "
           "skene.info/liitu?utm_source=ig_story")
    data = urllib.parse.urlencode({"chat_id": os.environ.get("TELEGRAM_CHAT_ID") or "1810496014",
                                   "caption": cap, "document": url}).encode()
    try:
        # sendDocument, mitte sendPhoto: Telegram ei pakista faili, kvaliteet jääb originaaliks
        urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendDocument", data=data, timeout=60)
        print("Telegrami saadetud")
    except Exception as e:
        print(f"Telegram ei õnnestunud: {type(e).__name__}")


if __name__ == "__main__":
    main()
