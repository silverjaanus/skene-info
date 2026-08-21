# -*- coding: utf-8 -*-
"""Regressioonitest: blokitud kirje manual.json-is peab KATKESTAMA korje.

Taust (21.08.2026 audit): blocklist filtreeris manual-kirjeid vaikselt —
Alma Negra tuli 14.08 sweepiga manual.json-i tagasi ja keegi ei marganud
enne 21.08, sest fetch trykkis ainult HOIATUSE (rap/klubi ei sedagi).
common.fail_if_manual_blocked teeb sellest kova vea. See test valvab, et
valve ka parast tulevasi refaktoreid alles jaaks ja oigesti pihta saaks.

Jookseb CI-s (checks.yml) ja lokaalselt: python scripts/test_blocklist_guard.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import fail_if_manual_blocked, slug

VIGU = 0


def ootab_viga(nimi, manual, block=set(), block_names=set(), block_artists=set()):
    global VIGU
    try:
        fail_if_manual_blocked(manual, block, block_names, block_artists, sait="test")
    except SystemExit:
        print(f"OK: {nimi} -> katkestas (oige)")
        return
    print(f"VIGA: {nimi} -> EI katkestanud, blokitud kirje laks labi!")
    VIGU += 1


def ootab_labi(nimi, manual, block=set(), block_names=set(), block_artists=set()):
    global VIGU
    try:
        fail_if_manual_blocked(manual, block, block_names, block_artists, sait="test")
    except SystemExit as ex:
        print(f"VIGA: {nimi} -> katkestas valesti: {ex}")
        VIGU += 1
        return
    print(f"OK: {nimi} -> labi (oige)")


E1 = {"d": "2026-09-04", "n": "Alma Negra", "b": ["Alma Negra"]}
E2 = {"d": "2026-10-01", "n": "Puhas Kirje", "b": ["Keegi Muu"]}

# 1. puhas manual laheb labi
ootab_labi("puhas manual", [E1, E2])

# 2. {d,n}-blokk: sama kirje samal paeval
ootab_viga("kuupaev+nimi blokk", [E1, E2],
           block={("2026-09-04", slug("Alma Negra"))})

# 3. {d,n}-blokk TEISEL paeval EI blokeeri
ootab_labi("kuupaev+nimi blokk teisel paeval", [E1, E2],
           block={("2026-09-05", slug("Alma Negra"))})

# 4. {n}-nimeblokk blokeerib igal kuupaeval
ootab_viga("nimeblokk", [E1, E2], block_names={slug("Alma Negra")})

# 5. artistiblokk pihtab b-massiivi kaudu
ootab_viga("artistiblokk (b-massiiv)", [E1, E2],
           block_artists={slug("Alma Negra")})

# 6. artistiblokk pihtab reliisipealkirja algust (>=8 marki)
E3 = {"d": "2026-11-01", "n": "Alma Negra — «Uus Album»", "b": []}
ootab_viga("artistiblokk (pealkirja algus)", [E3],
           block_artists={slug("Alma Negra")})

if VIGU:
    raise SystemExit(f"{VIGU} testi kukkus")
print("Koik blocklisti-valve testid labisid.")
