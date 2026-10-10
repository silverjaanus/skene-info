#!/usr/bin/env python3
"""Linnalehed otsimootoritele: www.skene.info/tallinn ja /tartu.

09.10.2026 kasvuplaan, etapp 4 (Google). Saidi pealehtede nimekiri tuleb
JavaScriptiga data.json-ist, seega Google naeb seal tuhja kesta ja
JSON-LD-d alles parast JS-i jooksutamist. Siin tehakse staatiline HTML:
koigi kolme saidi (metal/rap/klubi) tulevased uritused valitud linnas +
Event-strukturandmed (schema.org) otse lehe sees.

Jookseb iga paev update.yml-is (samm "Linnalehed") parast korjet.
Kasitsi:  python scripts/build_seo.py   (--check: valjumiskood 1, kui fail muutuks)

Valjund: tallinn.html, tartu.html (repo juurkaust). Teed /tallinn ja /tartu
tulevad vercel.json routes'ist. NB need failid on GENEREERITUD - ara muuda
kasitsi, muuda seda skripti.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_entries, today_local, end_date, next_start, is_release  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

SAIDID = [
    # (voti, data.json, pildikausta prefiks www-hostil, avalik host, pealkiri, alapealkiri)
    ("metal", ROOT / "data" / "data.json", "/", "https://www.skene.info", "Metal, punk ja rokk", "metal, punk, rokk, alternatiiv"),
    ("rap", ROOT / "rap" / "data" / "data.json", "/rap/", "https://rap.skene.info", "Räpp ja hiphop", "Eesti räpp ja hiphop"),
    ("klubi", ROOT / "klubi" / "data" / "data.json", "/klubi/", "https://klubi.skene.info", "Klubi", "tehno, bass ja klubiõhtud"),
]

LINNAD = {
    # slug: (c-vaartus, nimetav, seesütlev, omastav)
    "tallinn": ("Tallinn", "Tallinn", "Tallinnas", "Tallinna"),
    "tartu": ("Tartu", "Tartu", "Tartus", "Tartu"),
}

NADALAPAEV = ["E", "T", "K", "N", "R", "L", "P"]
KUU = ["jaanuar", "veebruar", "märts", "aprill", "mai", "juuni", "juuli", "august",
       "september", "oktoober", "november", "detsember"]


def esc(s):
    return html.escape(str(s or ""), quote=True)


def paev(iso):
    d = date.fromisoformat(iso)
    return f"{NADALAPAEV[d.weekday()]} {d.day:02d}.{d.month:02d}"


def linnas(e, c):
    """Kirje kuulub linna, kui c on see linn VOI c=mujal ja linn on see linn
    (andmetes on nt c=mujal + linn=Tartu)."""
    return e.get("c") == c or (e.get("linn") or "").strip() == c


def tulevased(entries, c, tana):
    out = []
    for e in entries:
        if not e.get("d") or e.get("tba") or is_release(e):
            continue
        if not linnas(e, c):
            continue
        try:
            if end_date(e) < tana.isoformat():
                continue
            naita = next_start(e, tana)
        except Exception:
            continue
        out.append((naita, e))
    out.sort(key=lambda x: (x[0], x[1].get("n", "")))
    return out


def url_ok(u):
    return bool(u) and re.match(r"^https?://", u) is not None


def hinnatekst(e):
    h = e.get("hind")
    if isinstance(h, dict):
        if "VÄLJA MÜÜDUD" in (h.get("mark") or "").upper():
            return "välja müüdud"
        return (h.get("praegu") or "").strip()
    return ""


def offer(e):
    pu = e.get("pu")
    if not url_ok(pu):
        return None
    o = {"@type": "Offer", "url": pu, "priceCurrency": "EUR"}
    h = e.get("hind") if isinstance(e.get("hind"), dict) else {}
    praegu = (h.get("praegu") or "").lower()
    if "VÄLJA MÜÜDUD" in (h.get("mark") or "").upper():
        o["availability"] = "https://schema.org/SoldOut"
    else:
        o["availability"] = "https://schema.org/InStock"
    # validFrom jaab teadlikult valja: muugi algust me ei tea.
    if praegu.startswith("tasuta"):
        o["price"] = "0"
    else:
        m = re.search(r"(\d+(?:[.,]\d{1,2})?)", praegu)
        if m:
            o["price"] = m.group(1).replace(",", ".")
    return o


LINGISILT = re.compile(r"^(facebook event|bandcamp|spotify|youtube|instagram|resident advisor|ra event|ametlik leht|"
                       r"ürituse leht|.*üritusleht|piletitasku|piletilevi|piletikeskus|fienta)$", re.I)
DOMEEN = re.compile(r"^[\w.-]+\.[a-z]{2,}$", re.I)


def korraldaja_nimi(s):
    """on_ on tihti lingi silt ("Facebook event", domeen), mitte korraldaja - need ei lahe organizer'iks."""
    s = (s or "").strip()
    return bool(s) and not LINGISILT.match(s) and not DOMEEN.match(s)


def ld_event(e, naita, linn_nimi, sait):
    _, _, pildiprefiks, host, _, _ = sait
    ev = {
        "@type": "Event",
        "name": e.get("n", ""),
        "startDate": naita,
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": {
            "@type": "Place",
            "name": e.get("v") or linn_nimi,
            "address": {"@type": "PostalAddress", "addressLocality": linn_nimi, "addressCountry": "EE"},
        },
    }
    lopp = end_date(e)
    ev["endDate"] = lopp if lopp > naita else naita
    u = e.get("ou") if url_ok(e.get("ou")) else e.get("su")
    if url_ok(u):
        ev["url"] = u
    if e.get("a"):
        ev["description"] = e["a"][:300]
    ev["image"] = [host + "/" + e["img"].lstrip("/") if e.get("img") else "https://www.skene.info/icons/cover.png"]
    if korraldaja_nimi(e.get("on_")):
        ev["organizer"] = {"@type": "Organization", "name": e["on_"]}
        if url_ok(e.get("ou")):
            ev["organizer"]["url"] = e["ou"]
    if e.get("b"):
        ev["performer"] = [{"@type": "PerformingGroup", "name": b} for b in e["b"][:12]]
    o = offer(e)
    if o:
        ev["offers"] = o
    return ev


def li(e, naita, sait):
    _, _, pildiprefiks, _, _, _ = sait
    s = paev(naita)
    lopp = end_date(e)
    if lopp > naita:
        s += "–" + paev(lopp)
    pilt = ""
    if e.get("img"):
        pilt = f'<img src="{esc(pildiprefiks + e["img"].lstrip("/"))}" alt="" width="64" height="64" loading="lazy" decoding="async">'
    else:
        pilt = '<span class="noimg" aria-hidden="true"></span>'
    rida = [f'<li class="ev">{pilt}<div class="txt">',
            f'<time datetime="{esc(naita)}">{esc(s)}</time>',
            f'<h3>{esc(e.get("n"))}</h3>']
    if e.get("v"):
        rida.append(f'<p class="koht">{esc(e["v"])}</p>')
    bandid = [b for b in (e.get("b") or []) if b]
    if bandid and not (len(bandid) == 1 and bandid[0].lower() in (e.get("n") or "").lower()):
        lisa = " · koosseis täieneb" if e.get("koosseis_tba") else ""
        rida.append(f'<p class="bandid">{esc(", ".join(bandid[:12]))}{esc(lisa)}</p>')
    lingid = []
    ou = e.get("ou") if url_ok(e.get("ou")) else (e.get("su") if url_ok(e.get("su")) else "")
    if ou:
        lingid.append(f'<a href="{esc(ou)}" rel="noopener" target="_blank">Ürituse leht</a>')
    if url_ok(e.get("pu")):
        lingid.append(f'<a href="{esc(e["pu"])}" rel="noopener" target="_blank">Piletid</a>')
    hind = hinnatekst(e)
    if hind:
        lingid.append(f'<span class="hind">{esc(hind)}</span>')
    if lingid:
        rida.append('<p class="lingid">' + " · ".join(lingid) + "</p>")
    rida.append("</div></li>")
    return "".join(rida)


def logo_svg():
    """Sama kastlogo mis /liitu lehel (uks allikas, et logo ei laheks lahku)."""
    try:
        t = (ROOT / "liitu.html").read_text(encoding="utf-8")
        m = re.search(r'<svg id="logo".*?</svg>', t, re.S)
        if m:
            return m.group(0)
    except Exception:
        pass
    return ""


CSS = """
:root{--paber:#F3F0E7;--tint:#1A1A1A;--hall:#5A564C;--joon:#8F8A7C;--bri:#D96A52;--hdrmuted:#A6A192;
--metal:#D96A52;--rap:#6E9BE0;--klubi:#A87FE8;
--sans:"Helvetica Neue",Helvetica,Arial,ui-sans-serif,sans-serif;--mono:ui-monospace,"SF Mono",Consolas,Menlo,monospace}
@font-face{font-family:"Anton";font-style:normal;font-weight:400;font-display:swap;src:url(/fonts/anton-latin.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:"Anton";font-style:normal;font-weight:400;font-display:swap;src:url(/fonts/anton-latin-ext.woff2) format("woff2");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--tint)}
body{color:var(--paber);font-family:var(--sans);font-size:16px;line-height:1.5}
a{color:inherit}
.wrap{max-width:720px;margin:0 auto;padding:22px 16px 48px}
.top{display:flex;align-items:center;gap:12px;border-bottom:3px solid var(--paber);padding-bottom:14px}
.brand{display:flex;align-items:center;gap:12px;text-decoration:none;min-width:0}
#logo{display:block;width:52px;height:52px;flex:none}
#logo .fr,#logo .sk,#logo .inf{fill:var(--paber)}
#logo .pl{fill:var(--bri)}
.umb{font-family:var(--mono);font-size:12px;letter-spacing:1px;color:var(--hdrmuted)}
.umb b{color:var(--paber)}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:var(--bri);margin:30px 0 10px}
h1{font-family:"Anton",var(--sans);font-weight:400;text-transform:uppercase;font-size:clamp(36px,8.5vw,60px);line-height:.98;margin-bottom:16px}
.lead{font-size:17px;color:#DCD8CC;max-width:56ch}
.hupe{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 6px}
.hupe a{font-family:var(--mono);font-size:13px;text-decoration:none;border:2px solid var(--wc);color:var(--wc);padding:5px 10px}
.hupe a:hover{background:var(--wc);color:var(--tint)}
section{margin-top:38px}
section h2{font-family:"Anton",var(--sans);font-weight:400;text-transform:uppercase;font-size:clamp(26px,6vw,36px);line-height:1;color:var(--wc);border-bottom:2px solid var(--wc);padding-bottom:8px;display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap}
section h2 a{font-family:var(--mono);font-size:12.5px;text-transform:none;letter-spacing:.3px;color:var(--hdrmuted);text-decoration:none;border-bottom:1px solid var(--joon)}
.c-metal{--wc:var(--metal)} .c-rap{--wc:var(--rap)} .c-klubi{--wc:var(--klubi)}
ul.list{list-style:none}
.ev{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #3A3833}
.ev img,.ev .noimg{flex:none;width:64px;height:64px;object-fit:cover;background:#2A2926}
.txt{min-width:0}
.ev time{font-family:var(--mono);font-size:13px;color:var(--wc)}
.ev h3{font-size:17px;line-height:1.3;font-weight:700;margin:2px 0}
.koht{font-size:14.5px;color:#DCD8CC}
.bandid{font-size:14px;color:var(--hdrmuted)}
.lingid{font-family:var(--mono);font-size:12.5px;color:var(--hdrmuted);margin-top:4px}
.lingid a{color:var(--paber);text-decoration:none;border-bottom:1px solid var(--joon)}
.cta{margin-top:40px;border:2px solid var(--paber);padding:18px}
.cta b{display:block;font-family:"Anton",var(--sans);font-weight:400;text-transform:uppercase;font-size:28px;line-height:1.05;color:var(--bri);margin-bottom:8px}
.cta a.btn{display:inline-block;margin-top:12px;font-family:var(--mono);font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;text-decoration:none;background:var(--bri);color:var(--tint);padding:12px 20px}
.cta a.btn:hover{background:var(--paber)}
.tyhi{color:var(--hdrmuted);margin-top:24px}
.foot{margin-top:36px;font-family:var(--mono);font-size:12px;color:var(--hdrmuted);line-height:1.8}
.foot a{color:var(--paber);text-decoration:none;border-bottom:1px solid var(--joon)}
"""


def leht(slug, tana):
    c, nimi, seesytlev, omastav = LINNAD[slug]
    sektsioonid, graaf, hupped, kokku = [], [], [], 0
    for sait in SAIDID:
        voti, path, _, host, pealkiri, _ = sait
        read = tulevased(load_entries(path), c, tana)
        if not read:
            continue
        kokku += len(read)
        hupped.append(f'<a class="c-{voti}" href="#{voti}">{esc(pealkiri)} ({len(read)})</a>')
        filtriga = f"{host}/?c={c}"
        items = "\n".join(li(e, naita, sait) for naita, e in read)
        sektsioonid.append(
            f'<section id="{voti}" class="c-{voti}"><h2>{esc(pealkiri)} '
            f'<a href="{esc(filtriga)}">filtrid ja kalender →</a></h2>\n<ul class="list">\n{items}\n</ul></section>')
        graaf.extend(ld_event(e, naita, nimi, sait) for naita, e in read)

    teine = [s for s in LINNAD if s != slug]
    teised = " · ".join(f'<a href="/{s}">{esc(LINNAD[s][3])} üritused</a>' for s in teine)
    url = f"https://www.skene.info/{slug}"
    title = f"Kontserdid ja peod {seesytlev}: metal, rokk, räpp, klubi | skene.info"
    desc = (f"{omastav} tulevased kontserdid, festivalid ja klubiõhtud ühes nimekirjas: metal, punk, rokk, "
            f"räpp ja elektrooniline muusika. Piletilingid ja hinnad, uueneb iga päev.")
    ld = json.dumps({"@context": "https://schema.org", "@graph": graaf}, ensure_ascii=False, separators=(",", ":"))
    ld = ld.replace("</", "<\\/")
    if sektsioonid:
        sisu = "\n".join(sektsioonid)
    else:
        sisu = f'<p class="tyhi">Praegu pole {omastav} kohta ühtegi tulevat üritust kirjas. Vaata kogu nimekirja <a href="https://www.skene.info/">skene.info</a> lehelt.</p>'
    kuupaev = f"{tana.day:02d}.{tana.month:02d}.{tana.year}"
    return f"""<!DOCTYPE html>
<html lang="et">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(f'Kontserdid ja peod {seesytlev} — skene.info')}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="SKENE.INFO">
<meta property="og:image" content="https://www.skene.info/icons/cover.png">
<link rel="icon" href="https://www.skene.info/icons/mail-logo-metal.png">
<script defer src="/_vercel/insights/script.js"></script>
<script type="application/ld+json">{ld}</script>
<style>{CSS}</style>
</head>
<body>
<!-- GENEREERITUD: scripts/build_seo.py ({kuupaev}). Ara muuda kasitsi. -->
<div class="wrap">
  <div class="top">
    <a class="brand" href="https://www.skene.info/" aria-label="skene.info avaleht">{logo_svg()}<span class="umb"><b>SKENE.INFO</b><br>Eesti UG-muusika ühest kohast</span></a>
  </div>
  <p class="eyebrow">{esc(nimi)} · {kokku} tulevast üritust</p>
  <h1>Kontserdid ja peod {esc(seesytlev)}</h1>
  <p class="lead">Kõik skene.info-sse kogutud {esc(omastav)} kontserdid, festivalid ja klubiõhtud ühel lehel: metal, punk, rokk, räpp ja elektrooniline muusika. Nimekiri uueneb iga päev.</p>
  <nav class="hupe" aria-label="Žanrid">{"".join(hupped)}</nav>
{sisu}
  <div class="cta"><b>Saa see nimekiri igal reedel postkasti</b>Järgmise nädala kontserdid ja peod ühes kirjas. Tasuta, loobuda saad igal ajal.<br><a class="btn" href="/liitu?ref=linn-{slug}">Telli nädalakiri →</a></div>
  <p class="foot">Vaata ka: {teised} · <a href="https://www.skene.info/">skene.info</a> · <a href="https://rap.skene.info/">rap.skene.info</a> · <a href="https://klubi.skene.info/">klubi.skene.info</a><br>Seis {kuupaev}. Kuupäevad ja hinnad võivad muutuda, kontrolli enne minekut ürituse lehelt.</p>
</div>
</body>
</html>
"""


def main():
    check = "--check" in sys.argv
    tana = today_local()
    muutus = False
    for slug in LINNAD:
        f = ROOT / f"{slug}.html"
        uus = leht(slug, tana)
        vana = f.read_text(encoding="utf-8") if f.exists() else ""
        if uus != vana:
            muutus = True
            if not check:
                f.write_text(uus, encoding="utf-8", newline="\n")
        print(f"{slug}.html: {'MUUTUS' if uus != vana else 'sama'}")
    if check and muutus:
        sys.exit(1)


if __name__ == "__main__":
    main()
