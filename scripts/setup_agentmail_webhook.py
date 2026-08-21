"""Loob (voi naitab) AgentMaili webhooki, mis toidab api/agentmail-hook.js't.

Kasutus repo juurest:
    python scripts/setup_agentmail_webhook.py --list      # naita olemasolevaid
    python scripts/setup_agentmail_webhook.py --create    # loo uus

Loeb saladused failist `.env` repo juures (gitignore'is: `.env` ja `.env.*`):
    AGENTMAIL_API_KEY=...
    AGENTMAIL_HOOK_SECRET=...
Need on TAPSELT samad vaartused, mis on Verceli keskkonnamuutujates.

Skript EI truki kunagi saladusi ega Svixi allkirjastamisvotit -- ainult webhooki
ID, aadressi ja tellitud sundmused.

MIKS eraldi skript, mitte konsooli UI: webhookide paneel konsoolis on sisse ehitatud
Svixi raam, kuhu automaatika ligi ei paase.
"""
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.agentmail.to/v0/webhooks"
URL = "https://www.skene.info/api/agentmail-hook"
EVENT = "message.received.unauthenticated"
HEADER = "X-Skene-Hook"

JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(JUUR, ".env")


def loe_env():
    if not os.path.exists(ENV):
        sys.exit("VIGA: faili .env ei ole. Vt skripti pais.")
    out = {}
    with open(ENV, "r", encoding="utf-8-sig") as f:
        for rida in f:
            rida = rida.strip()
            if not rida or rida.startswith("#") or "=" not in rida:
                continue
            k, _, v = rida.partition("=")
            out[k.strip()] = v.strip().strip('"').strip("'")
    puudu = [k for k in ("AGENTMAIL_API_KEY", "AGENTMAIL_HOOK_SECRET") if not out.get(k)]
    if puudu:
        sys.exit("VIGA: .env-is puudub: " + ", ".join(puudu))
    return out


def paring(meetod, url, votme, keha=None):
    andmed = json.dumps(keha).encode() if keha is not None else None
    req = urllib.request.Request(url, data=andmed, method=meetod)
    req.add_header("Authorization", "Bearer " + votme)
    if andmed:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]


def kokkuvote(w):
    # Teadlikult EI trukita `secret` ega `headers` valju.
    return "  {}  {}  events={}".format(
        w.get("webhook_id", "?"), w.get("url", "?"), w.get("event_types", "koik")
    )


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("--list", "--create", "--test"):
        sys.exit(__doc__)
    env = loe_env()
    votme = env["AGENTMAIL_API_KEY"]

    if sys.argv[1] == "--test":
        # Jaljendab AgentMaili sundmust ja saadab selle otse laivis olevale
        # endpointile. Katab kogu ahela peale Svixi kohaletoimetamise: saladuse
        # klapp Vercelis, saatjafilter, ja parisel AgentMaili API-le tehtav PATCH.
        # Thread ID tuleb kasurealt.
        if len(sys.argv) < 3:
            sys.exit("Kasutus: --test <thread_id>")
        keha = {
            "type": "event",
            "event_type": EVENT,
            "event_id": "evt_kasitsi_test",
            "message": {
                "inbox_id": "skene.info@agentmail.to",
                "thread_id": sys.argv[2],
                "message_id": "<test@example.com>",
                "labels": ["received", "unauthenticated"],
                "from": "Paavli Kultuurivabrik <info@kultuurivabrik.ee>",
            },
        }
        andmed = json.dumps(keha).encode()
        req = urllib.request.Request(URL, data=andmed, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header(HEADER, env["AGENTMAIL_HOOK_SECRET"])
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print("{}  {}".format(r.status, r.read().decode()[:300]))
        except urllib.error.HTTPError as e:
            print("{}  {}".format(e.code, e.read().decode()[:300]))
        return

    if sys.argv[1] == "--list":
        kood, vastus = paring("GET", API, votme)
        if kood != 200:
            sys.exit("VIGA {}: {}".format(kood, vastus))
        hooks = vastus.get("webhooks", [])
        print("Webhooke kokku: {}".format(len(hooks)))
        for w in hooks:
            print(kokkuvote(w))
        return

    kood, vastus = paring("GET", API, votme)
    if kood == 200:
        for w in vastus.get("webhooks", []):
            if w.get("url") == URL:
                print("JUBA OLEMAS, uut ei loodud:")
                print(kokkuvote(w))
                return

    kood, vastus = paring("POST", API, votme, {
        "url": URL,
        "event_types": [EVENT],
        "headers": {HEADER: env["AGENTMAIL_HOOK_SECRET"]},
        "client_id": "skene-unauthenticated-v1",
    })
    if kood not in (200, 201):
        sys.exit("VIGA {}: {}".format(kood, vastus))
    print("LOODUD:")
    print(kokkuvote(vastus))


if __name__ == "__main__":
    main()
