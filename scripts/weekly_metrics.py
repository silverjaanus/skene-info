# -*- coding: utf-8 -*-
"""weekly_metrics.py -- uudiskirja nadalanumbrid Notioni tabeli "skene.info nadalanumbrid" jaoks.

Loeb MailerLite API-st (token mailerlite_token.txt) ja prindib JSON-i:
  aktiivsed, kinnitamata, uued_7p (aktiivseks saanud viimase 7 paeva jooksul),
  allikad_7p / allikad_kokku (kliendivali `allikas`, loodud 09.10.2026),
  eelmine_kiri: avamis- ja klikimaar suurimast ambrist viimases saadetud kirjas,
  mis on vahemalt 1 paev vana (varskel kirjal statistika alles kogub).

Midagi ei muuda. IG/FB ja Verceli numbrid tulevad brauserist (vt ajastatud taski samm 7).

Kasutus:  python scripts/weekly_metrics.py [--repo .]
"""
import argparse, collections, datetime as dt, json, os, urllib.request

API = "https://connect.mailerlite.com/api"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    tok = open(os.path.join(a.repo, "mailerlite_token.txt"), encoding="utf-8").read().strip()
    H = {"Authorization": "Bearer " + tok, "Accept": "application/json"}

    def get(url):
        return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60).read())

    def subs(status):
        out, url = [], f"{API}/subscribers?limit=1000&filter[status]={status}"
        while url:
            d = get(url)
            out += d["data"]
            url = (d.get("links") or {}).get("next")
        return out

    now = dt.datetime.utcnow()
    wk = (now - dt.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    act, unc = subs("active"), subs("unconfirmed")
    src = lambda s: (s.get("fields") or {}).get("allikas") or "(puudub)"
    new7 = [s for s in act if (s.get("subscribed_at") or s.get("created_at") or "") >= wk]

    camps = get(f"{API}/campaigns?filter[status]=sent&limit=25")["data"]
    old = [c for c in camps if (c.get("finished_at") or "") and (c["finished_at"] <= (now - dt.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"))]
    prev = None
    if old:
        day = old[0]["finished_at"][:10]
        same = [c for c in old if c["finished_at"][:10] == day]
        big = max(same, key=lambda c: (c.get("stats") or {}).get("sent") or 0)
        st = big.get("stats") or {}
        prev = {"kuupaev": day, "saajaid": st.get("sent"),
                "avamismaar": (st.get("open_rate") or {}).get("float"),
                "klikimaar": (st.get("click_rate") or {}).get("float"),
                "kampaaniaid": len(same)}
        for k in ("avamismaar", "klikimaar"):
            if prev[k] is not None and prev[k] <= 1:
                prev[k] = round(prev[k] * 100, 2)

    print(json.dumps({
        "aeg_utc": now.strftime("%Y-%m-%d %H:%M"),
        "aktiivsed": len(act),
        "kinnitamata": len(unc),
        "uued_7p": len(new7),
        "allikad_7p": dict(collections.Counter(src(s) for s in new7)),
        "allikad_kokku": dict(collections.Counter(src(s) for s in act)),
        "eelmine_kiri": prev,
    }, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
