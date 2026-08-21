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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kirju", type=int, default=0, help="mitu kirja tana tootedeldi")
    ap.add_argument("--mcp-puudub", action="store_true",
                    help="AgentMaili MCP polnud sessioonis kattesaadav")
    ap.add_argument("--markus", default="")
    a = ap.parse_args()
    FAIL.write_text(json.dumps({
        "kuupaev": date.today().isoformat(),
        "kirju": a.kirju,
        "mcp": not a.mcp_puudub,
        "markus": a.markus,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if a.mcp_puudub:
        print("HOIATUS: elumark kirjutatud, aga MCP PUUDUS — postkast jai "
              "lugemata. Teata Silverile (Gmaili MCP kaudu, kui saadaval) ja "
              "logi HANDOVER §2 postkasti-plokki.")
    else:
        print(f"OK: elumark kirjutatud ({FAIL.name}, kirju {a.kirju}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
