#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pilt_sisendisse.py -- toob kasitsi korjatud pildid `pildid-sisend/`-i OIGE NIMEGA.

MIKS (Silveri otsus 31.08.2026): kasitsi pildisamm kais labi Chrome'i Downloadsi ja
ad hoc PowerShelli one-lineri, mis TOSTIS KOIK varsked .webp-id sisendkausta ilma
kontrollita. Kui failinimi ei klappinud uhegi kirje sluggiga, sattus fail kausta ja
`fetch_images.py` jattis ta vaikselt puutumata -- tulemus: "tegin pildi ara", aga kirje
oli endiselt pildita. See skript teeb sama too VALJENDATUD KONTROLLIGA.

⚠ MIKS MITTE base64/URL otse brauserist: `mcp__claude-in-chrome__javascript_tool`
filtreerib tagastusest nii base64-plokid ("BLOCKED: Base64 encoded data") kui
paringustringiga URL-id ("BLOCKED: Cookie/query string data") -- kontrollitud
31.08.2026. Seega on brauseri enda allalaadimine AINUS toimiv transport FB-kaante
jaoks; see skript teeb ulejaanud osa turvaliseks.

KOLM SISENDIT:
  --downloads         Downloadsist: liiguta varsked *.webp sisendkausta (vaikimisi 2 h)
  --fail  + --nimi    uks suvaline pildifail (nt vestlusest saadud plakat)
  --json              [{"n": "Kirje nimi", "b64": "..."} , ...] -- muudest allikatest

Igal juhul kontrollitakse, et failinimi/nimi vastab MONELE manual.json kirjele
(`common.slug`, sama mis `fetch_images.py`). Sobimatu fail JAAB PUUTUMATA ja
raporteeritakse. Lopus: `python scripts/fetch_images.py`.

Naited:
  python scripts/pilt_sisendisse.py --downloads
  python scripts/pilt_sisendisse.py --fail C:\\tmp\\plakat.png --nimi "Masta Robusta"
  python scripts/pilt_sisendisse.py --json sweep/_pildid.json
"""
import argparse, base64, io, json, os, re, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common import slug  # noqa: E402

SISEND = ROOT / "pildid-sisend"
MANUALID = ["data/manual.json", "rap/data/manual.json", "klubi/data/manual.json"]
PILDILAIENDID = (".webp", ".jpg", ".jpeg", ".png")


def kirjed():
    out = []
    for rel in MANUALID:
        p = ROOT / rel
        if not p.exists():
            continue
        for e in json.loads(p.read_text(encoding="utf-8")):
            n = str(e.get("n", ""))
            if n:
                out.append((slug(n), n, rel))
    return out


def leia_slug(nimi_voi_slug):
    """-> (slug, teade). None, kui ei sobitu tapselt uhe kirjega."""
    s = slug(nimi_voi_slug)
    if not s:
        return None, "nimest ei saa sluggi"
    koik = kirjed()
    tapne = [k for k in koik if k[0] == s]
    if len(tapne) >= 1:
        lisa = "" if len(tapne) == 1 else "HOIATUS: %d kirjet sama nimega" % len(tapne)
        return tapne[0][0], lisa
    algus = [k for k in koik if k[0].startswith(s)]
    if len(algus) == 1:
        return algus[0][0], "sobitus kirjega: %s" % algus[0][1]
    if len(algus) > 1:
        return None, "sobib %d kirjega (%s) - taps" % (
            len(algus), ", ".join(k[1][:35] for k in algus[:4]))
    return None, "uhtegi manual.json kirjet ei sobitunud"


def salvesta_baidid(nimi, toores, allikas=""):
    s, teade = leia_slug(nimi)
    if not s:
        return False, "VIGA  %-44s %s" % (str(nimi)[:44], teade)
    if len(toores) < 500:
        return False, "VIGA  %-44s pilt kahtlaselt vaike (%d B)" % (str(nimi)[:44], len(toores))
    mootmed = ""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(toores))
        im.verify()
        im2 = Image.open(io.BytesIO(toores))
        mootmed = " %dx%d" % im2.size
        laiend = "." + (im2.format or "webp").lower().replace("jpeg", "jpg")
    except Exception as ex:
        return False, "VIGA  %-44s ei ole loetav pilt: %s" % (str(nimi)[:44], ex)
    SISEND.mkdir(parents=True, exist_ok=True)
    fail = SISEND / (s + laiend)
    fail.write_bytes(toores)
    lisa = (" [%s]" % teade) if teade else ""
    return True, "OK    %-44s -> pildid-sisend/%s (%d B%s)%s%s" % (
        str(nimi)[:44], fail.name, len(toores), mootmed, lisa,
        (" <- " + allikas) if allikas else "")


def downloadsist(tunde):
    dl = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Downloads"
    if not dl.exists():
        return [(False, "VIGA  Downloads kausta ei leidnud: %s" % dl)]
    piir = time.time() - tunde * 3600
    kandidaadid = [f for f in dl.iterdir()
                   if f.is_file() and f.suffix.lower() in PILDILAIENDID
                   and f.stat().st_mtime > piir]
    if not kandidaadid:
        return [(False, "VIGA  Downloadsis ei ole viimase %g h jooksul uhtegi pilti. "
                        "Kas Chrome blokkis allalaadimise? Vaata aadressiriba ikooni." % tunde)]
    read = []
    for f in sorted(kandidaadid):
        s, teade = leia_slug(f.stem)
        if not s:
            read.append((False, "JATAN  %-43s %s (fail jaab Downloadsi)" % (f.name[:43], teade)))
            continue
        korras, rida = salvesta_baidid(f.stem, f.read_bytes(), allikas="Downloads/" + f.name)
        if korras:
            try:
                f.unlink()
            except Exception:
                pass
        read.append((korras, rida))
    return read


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", action="store_true", help="korja varsked pildid Downloadsist")
    ap.add_argument("--tunde", type=float, default=2.0, help="kui varsked (vaikimisi 2 h)")
    ap.add_argument("--fail", help="uks pildifail")
    ap.add_argument("--nimi", help="kirje nimi (voi selle algus)")
    ap.add_argument("--json", help='[{"n": ..., "b64": ...}, ...]')
    a = ap.parse_args()

    read = []
    if a.downloads:
        read += downloadsist(a.tunde)
    if a.fail:
        if not a.nimi:
            ap.error("--fail vajab ka --nimi")
        read.append(salvesta_baidid(a.nimi, Path(a.fail).read_bytes(), allikas=a.fail))
    if a.json:
        for x in json.loads(Path(a.json).read_text(encoding="utf-8")):
            nimi = x.get("n") or x.get("nimi")
            b64 = re.sub(r"^data:image/[a-z+]+;base64,", "", (x.get("b64") or "").strip(), flags=re.I)
            b64 = re.sub(r"\s+", "", b64)
            if not nimi or not b64:
                read.append((False, "VIGA  puudulik JSON-kirje"))
                continue
            try:
                read.append(salvesta_baidid(nimi, base64.b64decode(b64)))
            except Exception as ex:
                read.append((False, "VIGA  %-44s base64: %s" % (str(nimi)[:44], ex)))
    if not (a.downloads or a.fail or a.json):
        ap.error("anna --downloads VOI --fail+--nimi VOI --json")

    for _, rida in read:
        print(rida)
    ok = sum(1 for k, _ in read if k)
    vigu = len(read) - ok
    print("\nKOKKU: %d salvestatud, %d labi kukkunud. "
          "Jargmiseks: python scripts/fetch_images.py" % (ok, vigu))
    return 1 if vigu else 0


if __name__ == "__main__":
    sys.exit(main())
