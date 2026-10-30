"""Kas kandidaat on juba saidil? (TOOVOOG §1 reegel 21, 30.10.2026)

Otsib KÕIGIST kohtadest korraga: manual.json + data.json + data/archive/*.json + blocklist.json
kõigil kolmel saidil, nime JA esinejate järgi; --koht/--kp lisab sama koha + kuupäeva kontrolli.

Kasutus:
  python scripts/leia_olemas.py "patarei" "metallica" "danko jones"
  python scripts/leia_olemas.py --kp 2026-10-31 --koht hall
"""
import argparse, glob, io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SAIDID = {"www": "data", "rap": "rap/data", "klubi": "klubi/data"}


def lae(f):
    try:
        j = json.load(open(f, encoding="utf-8"))
    except Exception:
        return []
    if isinstance(j, dict):
        j = j.get("events") or next((v for v in j.values() if isinstance(v, list)), [])
    return j if isinstance(j, list) else []


def failid():
    for sait, p in SAIDID.items():
        yield sait, "manual", p + "/manual.json"
        yield sait, "data", p + "/data.json"
        yield sait, "BLOCKLIST", p + "/blocklist.json"
        for a in sorted(glob.glob(p + "/archive/*.json")):
            if not a.endswith("years.json"):
                yield sait, "arhiiv", a


def tekst(e):
    b = e.get("b") or []
    if not isinstance(b, list):
        b = [str(b)]
    return " ".join([str(e.get("n", "")), str(e.get("b", "")) if isinstance(e.get("b"), str) else " ".join(b),
                     str(e.get("su", "")), str(e.get("ou", "")), str(e.get("nb", ""))[:300]]).lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("otsing", nargs="*")
    ap.add_argument("--kp")
    ap.add_argument("--koht")
    a = ap.parse_args()
    for sait, kus, f in failid():
        for e in lae(f):
            t = tekst(e)
            tabas = [q for q in a.otsing if q.lower() in t]
            if a.kp and a.koht and e.get("d", "")[:10] == a.kp and a.koht.lower() in str(e.get("v", "")).lower():
                tabas.append("sama koht+kp")
            if tabas:
                print("%-5s %-9s %s | %s | %s | %s" % (sait, kus, e.get("d", "?"), e.get("n", "")[:60],
                                                      e.get("v", ""), ",".join(tabas)))


if __name__ == "__main__":
    main()
