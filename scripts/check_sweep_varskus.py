#!/usr/bin/env python3
"""Valvab, kas nadalane sweep on ULDSE joosnud.

MIKS (17.08.2026): kogu saidi sisu tuleb praktiliselt UHEST kohast -- reedesest
Chrome-sweepist, mis kirjutab manual.json-idesse. Serveripoolne korje annab
peasaidile ainult Krypti (13 kirjet), rapil ja klubil ei ole automaatseid
allikaid uldse (teadlik valik, vt fetch_rap.py / fetch_klubi.py paised).

Kui see uks task jaab joosmata -- taimer ei kaivitu, Chrome ei ava, sessioon
kukub -- EI YTLE SEDA KEEGI. Sait lihtsalt seisab ja naeb valja tapselt nagu
vaikne nadal. Sama muster, mis 17.08 kolm korda valja tuli: NULLI EI ERISTA
PUUDUVAST.

Siin loetakse koigi kolme manual.json-i koige varskem `lisatud` kuupaev. Kui
see on ule piiri vana, laheb skript punaseks -> Andmekorje job laheb punaseks
-> GitHub saadab Silverile kirja (sama tee, mida mooda 17.08 vea teade tuli).

Kasutus:
    python scripts/check_sweep_varskus.py            # piir 8 paeva
    python scripts/check_sweep_varskus.py --piir 12
    python scripts/check_sweep_varskus.py --hoiatus  # ei kuku, ainult teatab
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FAILID = [
    ("www", ROOT / "data" / "manual.json"),
    ("rap", ROOT / "rap" / "data" / "manual.json"),
    ("klubi", ROOT / "klubi" / "data" / "manual.json"),
]

# 8 paeva, mitte 7: sweep on REEDENE, seega ka oiges rutmis jooksu korral voib
# vahe olla kuni 7 paeva. 8 tahendab "uks reede jai paris vahele".
PIIR = 8


def viimane_lisatud(tee):
    """Koige varskem `lisatud` kuupaev failis. None, kui uhtegi pole."""
    try:
        d = json.loads(tee.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    ents = d["entries"] if isinstance(d, dict) and "entries" in d else d
    kuupaevad = []
    for e in ents:
        l = (e.get("lisatud") or "")[:10]
        if not l:
            continue
        try:
            kuupaevad.append(date.fromisoformat(l))
        except ValueError:
            continue
    return max(kuupaevad) if kuupaevad else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piir", type=int, default=PIIR,
                    help=f"lubatud vanus paevades (vaikimisi {PIIR})")
    ap.add_argument("--hoiatus", action="store_true", help="ara kuku, ainult teata")
    args = ap.parse_args()

    tana = date.today()
    seisud = []
    for sait, tee in FAILID:
        v = viimane_lisatud(tee)
        vanus = (tana - v).days if v else None
        seisud.append((sait, v, vanus))
        if v:
            print(f"  {sait:5s} viimane uus kirje {v} ({vanus} p tagasi)")
        else:
            print(f"  {sait:5s} MITTE UHTEGI `lisatud` kuupaeva")

    olemas = [s for s in seisud if s[1]]
    if not olemas:
        print("HOIATUS: uhestki manual.json-ist ei leitud `lisatud` kuupaeva "
              "— kontroll ei utle praegu midagi")
        return 0

    # koige varskem kirje YLE KOIGI saitide: sweep kirjutab neisse koigisse,
    # seega uks varske sait tahendab, et sweep ISE joosis.
    varskeim = min(s[2] for s in olemas)
    if varskeim <= args.piir:
        print(f"Sweep on varske: viimane uus kirje {varskeim} p tagasi (piir {args.piir} p).")
        # varske sisu != taielik labikaik — run-logi valve puuab osalist torget
        rl = run_log_kontroll(args.piir)
        return 0 if args.hoiatus else rl

    sonum = (f"Nadalane sweep ei ole {varskeim} paeva jooksul UHTEGI uut kirjet toonud "
             f"(piir {args.piir} p). Kontrolli, kas reedene task joosis: kas Chrome "
             f"avanes, kas sessioon kukkus, kas manual.json-id said push'itud.")
    if args.hoiatus:
        print(f"HOIATUS: {sonum}")
        return 0
    print(f"::error::{sonum}")
    return 1


def run_log_kontroll(piir):
    """Sweep-jooksu arvepidamise valve (21.08.2026 audit, ISEARMEERUV).

    `lisatud`-kontroll ulal naeb ainult TAIELIKKU vaikust — kui FB-seanss
    katkeb keset sweepi ja pool allikaid jaab labimata, tuleb ikkagi paar uut
    kirjet ja koik paistab roheline. Seetottu kirjutab sweep nuud iga jooksu
    lopus sweep/run-<kuupaev>.json (scripts/sweep_run_log.py, HANDOVER §2
    reegel 13): allikaid / avatud / skipitud+pohjus / uusi kirjeid.

    ISEARMEERUV: kuni yhtegi run-faili pole, ainult HOIATUS (uus kontract ei
    tohi minevikku punaseks varvida). Esimese run-faili ilmumisest alates on
    puuduv/vana fail VIGA -> punane -> kiri Silverile."""
    failid = sorted((ROOT / "sweep").glob("run-*.json"))
    if not failid:
        print("HOIATUS: sweep/run-*.json puudub veel — labikaigu-valve pole "
              "armeeritud. Esimene reedene sweep peab selle kirjutama "
              "(scripts/sweep_run_log.py, HANDOVER §2 reegel 13).")
        return 0
    uusim = failid[-1]
    try:
        d = json.loads(uusim.read_text(encoding="utf-8"))
        kp = date.fromisoformat(d["kuupaev"])
    except (ValueError, KeyError) as ex:
        print(f"::error::{uusim.name} ei parsinud ({ex}) — run-logi vorming katki")
        return 1
    vanus = (date.today() - kp).days
    if vanus > piir:
        print(f"::error::Viimane sweep-jooksu logi on {vanus} p vana ({uusim.name}, "
              f"piir {piir} p). Kas sweep jai vahele VOI jooksis, aga jattis "
              f"arvepidamise kirjutamata (HANDOVER §2 reegel 13) — molemad "
              f"vajavad pilku.")
        return 1
    skipitud = d.get("skipitud", [])
    print(f"Run-logi OK: {uusim.name}, avatud {d.get('avatud')}/{d.get('allikaid')}, "
          f"skipitud {len(skipitud)}, uusi {d.get('uusi')}.")
    for s in skipitud:
        print(f"  skipitud: {s.get('url')} ({s.get('pohjus')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
