#!/usr/bin/env python3
"""Otsib KAHTLASI DUPLIKAATE koigi kolme saidi andmetest.

Miks see olemas on (02.08.2026): saidile oli tekkinud mitu duplikaati, mida ukski
olemasolev kontroll ei puudnud:
  1. sama uritus kahest AUTO-allikast veidi eri nimega (HAINZ / Hainz ... TASUTA)
  2. manual.json-i lisatud kirje, mis oli juba olemas (Fuzzolini reliis)
  3. kirje 'd' muudeti -> archive_split sailitas ka vana kuupaevaga koopia (Kosmikud)
  4. manual.json-ist kustutatud kirje tuli eelmisest data.json-ist tagasi (Molbo, KRS-One)

Jooksuta PARAST fetch-skripte:
    python scripts/check_dupes.py
Valjundis on ainult KAHTLUSED - inimene otsustab. Valjumiskood 1, kui midagi leiti.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import slug  # noqa: E402

SAIDID = {
    "www": ROOT / "data",
    "rap": ROOT / "rap" / "data",
    "klubi": ROOT / "klubi" / "data",
}


LUBATUD_FAIL = ROOT / "data" / "dupe_ok.json"


def load(p):
    if not p.exists():
        return []
    raw = json.loads(p.read_text(encoding="utf-8"))
    return raw.get("entries", raw) if isinstance(raw, dict) else raw


def laadi_lubatud():
    """Teadlikult lubatud paarid (data/dupe_ok.json) - vt on_lubatud()."""
    lubatud = set()
    for k in load(LUBATUD_FAIL):
        lubatud.add((k["sait"], frozenset({slug(k["n1"]), slug(k["n2"])})))
    return lubatud


def on_lubatud(sait, a, b, lubatud):
    """Kas see paar on data/dupe_ok.json-is teadliku erandina kirjas?

    Lisatud 25.08.2026 (Silveri otsus). Pohjus: `leia_dupid` markib kahtlaseks ka
    kaks kirjet, mille ainus kokkulangevus on sama kuupaev + SAMA KOHT - see on
    tais-positiivne iga kord, kui uks maja teeb uhel ohtul kaks ERALDI PILETIGA
    uritust (A.V.R 28.08 Alexela Loomelava: 18.00 vanusepiiranguta ja 23.00 16+).
    Ilma erandita laheb "Kontrollid" punaseks kuni uritus arhiivi kukub.

    Vott on (sait, {slug(nimi1), slug(nimi2)}) - KUUPAEVA teadlikult ei ole votmes,
    sest kuupaeva muutumine on just see, mida check_dupes peab edasi puudma.
    Kui kumbki nimi muutub, lakkab erand kehtimast ja hoiatus tuleb tagasi -
    see on TAOTLETUD (fail-safe: aegunud erand ei vaiki uut probleemi maha).
    """
    votme = (sait, frozenset({slug(a.get("n", "")), slug(b.get("n", ""))}))
    return votme in lubatud


def bandset(e):
    return {slug(b) for b in e.get("b", []) if b}


def nimeleid(a, b):
    """Kas uks nimi sisaldub teises (slugi tasandil) - lyhikesed valistatud."""
    if len(a) < 8 or len(b) < 8:
        return False
    return a in b or b in a


def kirjeldus(e):
    osad = [e.get("d", "?")]
    if e.get("d2"):
        osad.append("-" + e["d2"])
    osad.append(e.get("n", "?"))
    if e.get("v"):
        osad.append("@ " + e["v"])
    if e.get("sn"):
        osad.append("[" + e["sn"] + "]")
    return " ".join(osad)


def leia_dupid(kirjed):
    """Kahtlus = SAMA kuupaev JA (nimeleid VOI bandi-kattuvus VOI sama venue)."""
    hits = []
    for i in range(len(kirjed)):
        for j in range(i + 1, len(kirjed)):
            a, b = kirjed[i], kirjed[j]
            if a.get("d") != b.get("d"):
                continue
            na, nb = slug(a.get("n", "")), slug(b.get("n", ""))
            if na == nb:
                hits.append(("SAMA NIMI", a, b))
                continue
            ba, bb = bandset(a), bandset(b)
            va, vb = slug(a.get("v", "") or ""), slug(b.get("v", "") or "")
            reliisid = a.get("t") == "reliis" and b.get("t") == "reliis"
            if nimeleid(na, nb):
                hits.append(("nimi sisaldub", a, b))
            elif ba and bb and (ba & bb):
                hits.append(("sama band: " + ", ".join(sorted(ba & bb)), a, b))
            elif va and va == vb and not reliisid:
                # NB: kaks reliisi samal paeval jagavad 'v' valja ("Bandcamp") -
                # see EI ole duplikaat, seega reliiside puhul kohareeglit ei rakenda
                hits.append(("sama koht", a, b))
    return hits


def leia_sarjad(kirjed):
    """Kahtlus ULE KUUPAEVADE: uhe kirje nimi sisaldub taielikult teise omas.
    Nii jaab vahele sama sari kahes kirjes eri kuupaevadega - naiteks
    'Plaaditurg: TOUR DE PLAAT 2026' vs 'Augustibluusi Plaaditurg (TOUR DE PLAAT 2026)'
    (Silveri leid 02.08.2026, leia_dupid ei puudnud, sest kuupaevad erinesid).
    Lavend 14 tahemarki hoiab lyhikeste nimede juhusliku kattumise eemal."""
    hits = []
    for i in range(len(kirjed)):
        for j in range(i + 1, len(kirjed)):
            a, b = kirjed[i], kirjed[j]
            if a.get("d") == b.get("d"):
                continue  # need puuab juba leia_dupid
            # reliis + sama nimega kontsert (albumiesitlus) EI ole duplikaat
            if (a.get("t") == "reliis") != (b.get("t") == "reliis"):
                continue
            na, nb = slug(a.get("n", "")), slug(b.get("n", ""))
            if len(na) < 14 or len(nb) < 14:
                continue
            if na == nb:
                # Sama nimi + eri kuupaev on tugev margk sellest, et kellegi 'd' muudeti
                # ja vana koopia jai eelmisest data.json-ist alles (vt archive_split).
                # AGA sama band voib paris elus mangida kahel jarjestikusel paeval eri
                # kohtades (Sudden Lights 29.10 Fotografiska + 30.10 Genialistide) -
                # seega margi ainult siis, kui ka KOHT on sama voi puudub.
                va2, vb2 = slug(a.get("v", "") or ""), slug(b.get("v", "") or "")
                if va2 == vb2 or not va2 or not vb2:
                    hits.append(("SAMA NIMI + sama koht, eri kuupaev - tonaoliselt 'd' muudeti", a, b))
            elif na in nb or nb in na:
                hits.append(("sama sari, eri kuupaev", a, b))
    return hits


def leia_kadunud(sait, kaust):
    """manual.json-ist puuduvad, aga data.json-is olevad KURATEERITUD kirjed.
    Need on tavaliselt eelmisest data.json-ist sailinud kummitused (vt archive_split)."""
    manual = load(kaust / "manual.json")
    data = load(kaust / "data.json")
    man_keys = {(e.get("d"), slug(e.get("n", ""))) for e in manual}
    auto_sn = {"Metal Storm", "The Krypt FB", "thekrypt.ee", "paavli.ee", "helitehas.ee"}
    kummitused = []
    for e in data:
        k = (e.get("d"), slug(e.get("n", "")))
        if k in man_keys:
            continue
        if e.get("sn") in auto_sn:
            continue  # tuleb auto-allikast, normaalne
        kummitused.append(e)
    return kummitused


def main():
    vigu = 0
    lubatud = laadi_lubatud()
    for sait, kaust in SAIDID.items():
        data = load(kaust / "data.json")
        print(f"\n=== {sait} ({len(data)} kirjet data.json-is) ===")

        koik = leia_dupid(data) + leia_sarjad(data)
        hits = [h for h in koik if not on_lubatud(sait, h[1], h[2], lubatud)]
        vaigistatud = len(koik) - len(hits)
        if vaigistatud:
            print(f"  ({vaigistatud} paari vaigistatud data/dupe_ok.json kaudu)")
        if hits:
            vigu += len(hits)
            print(f"  KAHTLASI DUPLIKAATE: {len(hits)}")
            for pohjus, a, b in hits:
                print(f"   - [{pohjus}]")
                print(f"       A: {kirjeldus(a)}")
                print(f"       B: {kirjeldus(b)}")
        else:
            print("  duplikaate ei leitud")

        kumm = leia_kadunud(sait, kaust)
        if kumm:
            vigu += len(kumm)
            print(f"  KUMMITUSI (data.json-is, aga mitte manual.json-is ega tuntud auto-allikast): {len(kumm)}")
            for e in kumm:
                print(f"   - {kirjeldus(e)}")

    # 13.08.2026 audit: GENRE_META synkikontroll jookseb sama varavaga (paevane
    # workflow + kasitsi jooksud), et Python/JS koopiad ei triiviks margatamatult.
    try:
        import check_meta_sync
        vigu += check_meta_sync.main()
    except Exception as ex:
        print(f"HOIATUS: meta-sync kontroll ei jooksnud: {type(ex).__name__}: {ex}")

    if vigu:
        print(f"\nKOKKU {vigu} kahtlust. Kummituse kustutamiseks lisa blocklist.json-i "
              "kirje vana 'd' + 'n'-ga ja jooksuta fetch uuesti.")
        return 1
    print("\nKoik puhas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
