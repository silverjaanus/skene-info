#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ig_publish.py -- postitab tanase Instagrami story (kasvuplaan, etapp 2, 09.10.2026).

Make.com-il pole story-moodulit, seega postitame otse Instagrami API-ga
(Meta Graph API, content publishing). Jookseb GitHub Actionsis
(.github/workflows/ig_story.yml) iga paev ~10:00.

Postitab AINULT siis, kui:
  - ig/today.json["date"] == tana (Europe/Tallinn)
  - ig/today.json["story"]["postita"] == true  (luliti: data/ig_seaded.json)
  - tanast storyt pole veel postitatud (ig/postitatud.json)
  - keskkonnas on IG_TOKEN (lehe paasuvoti; GitHubi secret, seda EI hoita repos)

Kasutus:  python scripts/ig_publish.py [--dry-run]
"""
import argparse, datetime as dt, json, os, sys, time, urllib.parse, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import today_local

IG_USER_ID = "17841409504581888"     # @skene.info (sama, mida Make kasutab)
GRAPH = "https://graph.facebook.com"


def call(method, path, params):
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(f"{GRAPH}/{path}?{data.decode()}")
    else:
        req = urllib.request.Request(f"{GRAPH}/{path}", data=data, method="POST")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        sys.exit(f"VIGA {e.code} {path}: {body[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

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

    token = os.environ.get("IG_TOKEN", "").strip()
    if not token:
        print("IG_TOKEN puudub (GitHubi secret seadistamata) -- ei postita."); return
    if a.dry_run:
        print(f"DRY-RUN: postitaksin {st['image_url']}"); return

    c = call("POST", f"{IG_USER_ID}/media", {"image_url": st["image_url"], "media_type": "STORIES", "access_token": token})
    cid = c["id"]
    for _ in range(20):
        s = call("GET", cid, {"fields": "status_code", "access_token": token}).get("status_code")
        if s == "FINISHED":
            break
        if s == "ERROR":
            sys.exit(f"VIGA: Instagram ei suutnud pilti töödelda ({st['image_url']})")
        time.sleep(3)
    p = call("POST", f"{IG_USER_ID}/media_publish", {"creation_id": cid, "access_token": token})
    log[today] = {"media_id": p.get("id"), "image_url": st["image_url"]}
    # hoia logi lühike (30 päeva)
    keep = sorted(log)[-30:]
    log = {k: log[k] for k in keep}
    with open(logp, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"OK: story postitatud, media_id {p.get('id')}")


if __name__ == "__main__":
    main()
