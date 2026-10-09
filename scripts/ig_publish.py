#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ig_publish.py -- postitab tanase Instagrami story (kasvuplaan, etapp 2, 09.10.2026).

Make.com-il pole story-moodulit, seega postitame otse Instagrami API-ga
(Zernio API, sest Meta arendajakonto jai SMS-i taha). Jookseb GitHub Actionsis
(.github/workflows/ig_story.yml) iga paev ~10:00.

Postitab AINULT siis, kui:
  - ig/today.json["date"] == tana (Europe/Tallinn)
  - ig/today.json["story"]["postita"] == true  (luliti: data/ig_seaded.json)
  - tanast storyt pole veel postitatud (ig/postitatud.json)
  - keskkonnas on ZERNIO_API_KEY (GitHubi secret, seda EI hoita repos);
    valikuline ZERNIO_ACCOUNT_ID, muidu leitakse uhendatud Instagrami konto ise

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


ZERNIO = "https://zernio.com/api/v1"


def zernio(method, path, key, body=None):
    req = urllib.request.Request(f"{ZERNIO}/{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                                          "Accept": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=120)
        return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"VIGA Zernio {e.code} {path}: {e.read().decode('utf-8', 'replace')[:500]}")


def zernio_ig_account(key):
    """Leia ühendatud Instagrami konto id (kui ZERNIO_ACCOUNT_ID pole antud)."""
    _, d = zernio("GET", "accounts", key)
    items = d.get("accounts") if isinstance(d, dict) else d
    for x in items or []:
        if (x.get("platform") or "").lower() == "instagram":
            return x.get("_id") or x.get("id")
    sys.exit(f"VIGA: Zernios pole Instagrami kontot ühendatud ({json.dumps(d)[:300]})")


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

    # 09.10.2026: Meta arendajakonto jäi SMS-i taha (vt HANDOVER-ARCHIVE 08.07),
    # seega postitame Zernio (endine Late) kaudu. Tasuta pakett = 10 postitust kuus,
    # sellepärast käib automaatika ainult T + N; laupäeva story teeb Silver ise.
    key = os.environ.get("ZERNIO_API_KEY", "").strip()
    if not key:
        print("ZERNIO_API_KEY puudub (GitHubi secret seadistamata) -- ei postita."); return
    if a.dry_run:
        print(f"DRY-RUN: postitaksin {st['image_url']}"); return

    acc = os.environ.get("ZERNIO_ACCOUNT_ID", "").strip() or zernio_ig_account(key)
    body = {"mediaItems": [{"type": "image", "url": st["image_url"]}],
            "platforms": [{"platform": "instagram", "accountId": acc,
                           "platformSpecificData": {"contentType": "story"}}],
            "publishNow": True}
    code, p = zernio("POST", "posts", key, body)
    post = p.get("post", p)
    plats = post.get("platforms") or p.get("platforms") or []
    if code != 201 or post.get("status") not in ("published", None):
        errs = "; ".join(str(x.get("errorMessage")) for x in plats if x.get("errorMessage"))
        sys.exit(f"VIGA Zernio {code}: status={post.get('status')} {errs or json.dumps(p)[:400]}")
    url = next((x.get("platformPostUrl") for x in plats if x.get("platformPostUrl")), None)
    log[today] = {"zernio_post": post.get("_id") or post.get("id"), "url": url, "image_url": st["image_url"]}
    # hoia logi lühike (30 päeva)
    keep = sorted(log)[-30:]
    log = {k: log[k] for k in keep}
    with open(logp, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"OK: story postitatud {url or ''}")


if __name__ == "__main__":
    main()
