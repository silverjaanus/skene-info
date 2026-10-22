#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inbox_heartbeat.py -- postkastijooksu elumark (21.08.2026 audit).

MIKS: 20.08.2026 jai igapaevane postkastijooks TAIELIKULT tegemata (AgentMaili
MCP polnud sessioonis uhendatud) ja seda ei oelnud keegi -- "0 uut kirja" ja
"jooks ei kaivitunudki" olid eristamatud. Sel korral vedas (kirju polnudki),
aga kontaktivormi kiri oleks jaanud vaikselt seisma.

MIDA: postkasti-task (skene-contact-inbox-check) jooksutab selle skripti IGA
jooksu lopus -- KA vaiksel paeval ja KA siis, kui AgentMaili MCP puudub.
Kirjutab sweep/inbox_heartbeat.json (gitignore'itud, ainult lokaalne).
Reedene sweep-fetch (common.warn_inbox_heartbeat) hoiatab, kui elumark on
ule 2 paeva vana voi utleb "mcp": false -- siis on postkastivalve katki ja
sweep-agent PEAB selle kokkuvottesse + hommikumeili panema.

Kasutus (postkasti-task, alati viimane samm):
  python scripts/inbox_heartbeat.py --kirju 0            # vaikne paev
  python scripts/inbox_heartbeat.py --kirju 3            # 3 kirja tootedeldud
  python scripts/inbox_heartbeat.py --mcp-puudub         # AgentMail MCP polnud!
"""
import argparse, json, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAIL = ROOT / "sweep" / "inbox_heartbeat.json"


AVALIK = ROOT / "valvur" / "postkast.json"


def avalik(sisu):
    """22.10.2026: elumark ka repo-sse (valvur/postkast.json), et pilves jooksev valvur
    (Claude'i ajastatud ulesanne, iga paev 16:00) naeks, kas postkastijooks toimus.
    Commitib AINULT selle faili; viga siin ei peata midagi."""
    import subprocess
    AVALIK.parent.mkdir(exist_ok=True)
    AVALIK.write_text(sisu, encoding="utf-8")
    g = ["git", "-C", str(ROOT)]
    try:
        subprocess.run(g + ["add", "valvur/postkast.json"], check=True, capture_output=True)
        if subprocess.run(g + ["diff", "--cached", "--quiet", "--", "valvur/postkast.json"]).returncode == 0:
            return
        subprocess.run(g + ["commit", "-m", "valvur: postkast " + date.today().isoformat(),
                            "--", "valvur/postkast.json"], check=True, capture_output=True)
        subprocess.run(g + ["pull", "--rebase", "--autostash", "-q", "origin", "main"], check=True, capture_output=True)
        subprocess.run(g + ["push", "-q", "origin", "main"], check=True, capture_output=True)
        print("OK: elumark pushitud (valvur/postkast.json).")
    except subprocess.CalledProcessError as e:
        print("HOIATUS: elumargi push ebaonnestus: %s" % (e.stderr or b"").decode("utf-8", "replace")[:300])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kirju", type=int, default=0, help="mitu kirja tana tootedeldi")
    ap.add_argument("--mcp-puudub", action="store_true",
                    help="AgentMaili MCP polnud sessioonis kattesaadav")
    ap.add_argument("--markus", default="")
    a = ap.parse_args()
    sisu = json.dumps({
        "kuupaev": date.today().isoformat(),
        "kirju": a.kirju,
        "mcp": not a.mcp_puudub,
        "markus": a.markus,
    }, ensure_ascii=False, indent=1) + "\n"
    FAIL.write_text(sisu, encoding="utf-8")
    avalik(sisu)
    if a.mcp_puudub:
        print("HOIATUS: elumark kirjutatud, aga MCP PUUDUS — postkast jai "
              "lugemata. Teata Silverile (Gmaili MCP kaudu, kui saadaval) ja "
              "logi HANDOVER §2 postkasti-plokki.")
    else:
        print(f"OK: elumark kirjutatud ({FAIL.name}, kirju {a.kirju}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
