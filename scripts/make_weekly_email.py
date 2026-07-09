#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_weekly_email.py -- genereerib skene.info nadalameili (HTML, email-safe), ET + EN.

Loeb data/data.json, filtreerib sama akna mis make_weekly_image (see + jargmine
nadal, Eesti kirjed). Toodab kaks HTML-faili: <out>.et.html ja <out>.en.html.
Ainult liides (chrome) tolgitakse; URITUSTE ANDMED jaavad eesti keeles.

Valikuline: --send saadab MailerLite'i API kaudu kampaania per keele-segment
(token failist, konfiguratsioon mailerlite_config.json-ist). Ilma --send liputa
midagi ei saadeta -- ainult failid.

Kasutus:
  python make_weekly_email.py --data <data.json> --out <email> [--date YYYY-MM-DD]
  python make_weekly_email.py --data <data.json> --out <email> --send \\
      --token-file mailerlite_token.txt --config mailerlite_config.json
"""
import argparse, json, os, sys, html, datetime as dt
import urllib.request, urllib.error

# ---- palett (index.html :root) ----
PABER="#F3F0E7"; TINT="#1A1A1A"; HALL="#5A564C"; JOON="#8F8A7C"
KAART="#FBFAF5"
TELLISKIVI="#93392C"; PLOOM="#4E4275"; SINEP="#A8811F"; PAATINA="#2C5B54"
TYPE_COLOR={"kontsert":TELLISKIVI,"festival":SINEP,"klubi":PLOOM,"reliis":PAATINA,"merch":PAATINA}
EESTI={"Tallinn","Tartu","mujal"}
# Multi-uudiskirja cross-promo ("Sa tellid ainult metal-uudiskirja...") on praegu VÄLJAS.
# Lisa uuesti (kirja LÕPPU) kui rap/kino/dj saidid on päriselt tööle läinud → True.
SHOW_CROSS_PROMO=False
SITE_URL="https://www.skene.info/"

# ---- chrome i18n (ainult liides; ANDMED jaavad ET) ----
I18N={
 "et":{
  "lang_attr":"et",
  "kicker":"SKENE.INFO &middot; Eesti alternatiiv",
  "title":"Tulevad üritused",
  "site_cta":"Kõik üritused &amp; artistid &rarr; skene.info",
  "entry_1":"kirje","entry_n":"kirjet",
  "type":{"kontsert":"KONTSERT","festival":"FESTIVAL","klubi":"KLUBI","reliis":"UUS RELIIS","merch":"MERCH"},
  "wday":["E","T","K","N","R","L","P"],
  "new":"uus",
  "ticket_lbl":"Pilet: ","buy":"osta pilet &rarr;",
  "months":{1:"jaanuar",2:"veebruar",3:"märts",4:"aprill",5:"mai",6:"juuni",7:"juuli",
            8:"august",9:"september",10:"oktoober",11:"november",12:"detsember"},
  "promo_h":"Sa tellid ainult metal-uudiskirja.",
  "promo_b":"Meil on ka <b>rap.skene.info</b> uudiskiri (peagi lisanduvad kino ja dj). "
            "Vali teemad juurde &mdash; kõik tuleb ühes kirjas, ilma et postkast täituks. "
            "Iga teema saab eraldi välja lülitada.",
  "promo_btn":"Halda teemasid &rarr;",
  "foot_tag":"üritused &middot; reliisid &middot; merch &middot; uudiskiri korra nädalas",
  "foot_prefs":"Halda eelistusi","foot_unsub":"Loobu",
  "foot_why":"Saad seda kirja, sest liitusid skene.info uudiskirjaga ja kinnitasid tellimuse.",
  "subject":"skene.info nädalakiri &mdash; {range}",
 },
 "en":{
  "lang_attr":"en",
  "kicker":"SKENE.INFO &middot; Estonian alternative",
  "title":"Upcoming events",
  "site_cta":"All events &amp; artists &rarr; skene.info",
  "entry_1":"entry","entry_n":"entries",
  "type":{"kontsert":"CONCERT","festival":"FESTIVAL","klubi":"CLUB","reliis":"NEW RELEASE","merch":"MERCH"},
  "wday":["Mo","Tu","We","Th","Fr","Sa","Su"],
  "new":"new",
  "ticket_lbl":"Ticket: ","buy":"buy ticket &rarr;",
  "months":{1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",7:"July",
            8:"August",9:"September",10:"October",11:"November",12:"December"},
  "promo_h":"You're subscribed to the metal newsletter only.",
  "promo_b":"We also run a <b>rap.skene.info</b> newsletter (cinema and dj coming soon). "
            "Add topics &mdash; everything arrives in one email without flooding your inbox. "
            "Each topic can be switched off separately.",
  "promo_btn":"Manage topics &rarr;",
  "foot_tag":"events &middot; releases &middot; merch &middot; new every week",
  "foot_prefs":"Manage preferences","foot_unsub":"Unsubscribe",
  "foot_why":"You're receiving this because you subscribed to the skene.info newsletter and confirmed it.",
  "subject":"skene.info weekly &mdash; {range}",
 },
}

def parse_d(s): return dt.date.fromisoformat(s)

def event_span(e):
    start=parse_d(e["d"])
    if e.get("d2"):
        dd,mm=e["d2"].split("."); end=dt.date(start.year,int(mm),int(dd))
        if end<start: end=dt.date(start.year+1,int(mm),int(dd))
        return start,end
    return start,start

def this_and_next_week(ref):
    wd=ref.weekday()
    return ref, ref+dt.timedelta(days=(13-wd))

def in_window(e,ws,we):
    s,en=event_span(e)
    return s<=we and en>=ws

def esc(s): return html.escape(s or "")

def price_text(e):
    h=e.get("hind")
    if not h: return None
    p=(h.get("praegu") or "").strip()
    if not p and h.get("mark"): p=str(h["mark"]).strip()
    return p or None

def title_link(e):
    return e.get("ou") or e.get("su") or ""

def event_row(e, L):
    s,en=event_span(e)
    t=e.get("t","")
    col=TYPE_COLOR.get(t,HALL)
    label=L["type"].get(t,t.upper())
    is_rel = t in ("reliis","merch") or e.get("rel")
    datebig=f"{s.day:02d}.{s.month:02d}"
    if is_rel:
        wl=L["new"]
    else:
        wl=L["wday"][s.weekday()]
        if e.get("d2"): wl+=f"&ndash;{en.day:02d}.{en.month:02d}"
    tagfg = TINT if col==SINEP else "#FFFFFF"
    tag=(f'<span style="display:inline-block;background:{col};color:{tagfg};'
         f'font:700 11px/1.4 \'Courier New\',monospace;letter-spacing:.5px;'
         f'padding:2px 7px;">{label}</span>')
    name=esc(e.get("n",""))
    link=title_link(e)
    if link:
        name=(f'<a href="{esc(link)}" style="color:{TINT};text-decoration:none;'
              f'border-bottom:1px solid {JOON};">{name}</a>')
    title=f'<div style="font:700 17px/1.3 Arial,Helvetica,sans-serif;color:{TINT};margin:6px 0 0;">{name}</div>'
    bands=" &middot; ".join(esc(b) for b in e.get("b",[])) if e.get("b") else esc(e.get("a",""))
    bands_html=(f'<div style="font:400 13px/1.4 \'Courier New\',monospace;color:{HALL};margin:3px 0 0;">{bands}</div>' if bands else "")
    venue=esc(e.get("v",""))
    linn=e.get("linn") or ("" if e.get("c")=="mujal" else e.get("c",""))
    loc=venue+(", "+esc(linn) if linn and esc(linn).lower() not in venue.lower() else "")
    pt=price_text(e); pu=e.get("pu")
    price_bits=[]
    if pt:
        lbl = "" if is_rel else L["ticket_lbl"]
        price_bits.append(f'<span style="color:{PAATINA};font:700 13px/1.4 \'Courier New\',monospace;">{lbl}{esc(pt)}</span>')
    if pu:
        price_bits.append(f'<a href="{esc(pu)}" style="color:{PAATINA};font:700 12px/1.4 \'Courier New\',monospace;">{L["buy"]}</a>')
    price_html=" &nbsp; ".join(price_bits)
    loc_line=(f'<div style="font:700 14px/1.4 Arial,Helvetica,sans-serif;color:{TINT};margin:5px 0 0;">{loc}'
              + (f'<span style="float:right;font-weight:400;">{price_html}</span>' if price_html else "")
              + '</div>')
    return f"""
      <tr>
        <td width="74" valign="top" style="padding:14px 0 14px 0;border-top:1px solid {JOON};">
          <div style="font:700 20px/1 'Courier New',monospace;color:{TINT};">{datebig}</div>
          <div style="font:400 12px/1.4 'Courier New',monospace;color:{HALL};margin-top:3px;">{wl}</div>
        </td>
        <td valign="top" style="padding:14px 0 14px 14px;border-top:1px solid {JOON};">
          {tag}{title}{bands_html}{loc_line}
        </td>
      </tr>"""

def daterange(ws,we,L):
    M=L["months"]
    if ws.month==we.month:
        return f"{ws.day}.&ndash;{we.day}. {M[ws.month]} {we.year}"
    return f"{ws.day}. {M[ws.month]} &ndash; {we.day}. {M[we.month]} {we.year}"

def build_html(entries, ws, we, lang):
    L=I18N[lang]
    rows="".join(event_row(e, L) for e in entries)
    n=len(entries); krje=L["entry_1"] if n==1 else L["entry_n"]
    rng=daterange(ws,we,L)
    promo_html=""
    if SHOW_CROSS_PROMO:
        promo_html=f"""  <!-- multi-teema cross-promo (kirja lopus; sees kui uued saidid valmis) -->
  <tr><td style="padding:8px 28px 22px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PABER};border:1px dashed {JOON};">
      <tr><td style="padding:16px 18px;">
        <div style="font:700 14px/1.4 Arial,Helvetica,sans-serif;color:{TINT};">{L['promo_h']}</div>
        <div style="font:400 13px/1.5 Arial,Helvetica,sans-serif;color:{HALL};margin:4px 0 12px;">{L['promo_b']}</div>
        <a href="{SITE_URL}" style="display:inline-block;background:{TINT};color:{PABER};font:700 13px/1 Arial,Helvetica,sans-serif;text-decoration:none;padding:11px 18px;">{L['promo_btn']}</a>
      </td></tr>
    </table>
  </td></tr>"""
    return f"""<!DOCTYPE html>
<html lang="{L['lang_attr']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>skene.info</title></head>
<body style="margin:0;padding:0;background:{PABER};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PABER};">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:{KAART};border:1px solid {JOON};">

  <!-- pais -->
  <tr><td style="padding:26px 28px 8px;">
    <div style="font:400 12px/1.4 'Courier New',monospace;letter-spacing:1px;color:{HALL};text-transform:uppercase;">{L['kicker']}</div>
    <div style="font:800 34px/1.05 Arial,Helvetica,sans-serif;color:{TINT};margin:6px 0 0;letter-spacing:-.5px;">{L['title']}</div>
    <div style="font:400 14px/1.4 'Courier New',monospace;color:{TELLISKIVI};margin:8px 0 0;">{rng} &middot; {n} {krje}</div>
    <div style="margin:14px 0 2px;"><a href="{SITE_URL}" style="display:inline-block;font:700 12px/1 'Courier New',monospace;color:{PABER};background:{TELLISKIVI};text-decoration:none;padding:9px 14px;letter-spacing:.3px;">{L['site_cta']}</a></div>
  </td></tr>

  <!-- uritused -->
  <tr><td style="padding:12px 28px 4px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}
      <tr><td colspan="2" style="border-top:1px solid {JOON};font-size:0;line-height:0;">&nbsp;</td></tr>
    </table>
  </td></tr>

{promo_html}
  <!-- footer -->
  <tr><td style="background:{TINT};padding:20px 28px;">
    <div style="font:800 18px/1 Arial,Helvetica,sans-serif;color:{PABER};">skene.info</div>
    <div style="font:400 12px/1.5 'Courier New',monospace;color:{JOON};margin:6px 0 0;">{L['foot_tag']}</div>
    <div style="font:400 12px/1.6 Arial,Helvetica,sans-serif;color:{JOON};margin:12px 0 0;">
      <a href="https://www.skene.info/privaatsus.html" style="color:{PABER};">{L['foot_prefs']}</a> &nbsp;·&nbsp;
      <a href="{{$unsubscribe}}" style="color:{PABER};">{L['foot_unsub']}</a>
    </div>
    <div style="font:400 11px/1.5 Arial,Helvetica,sans-serif;color:{HALL};margin:10px 0 0;">{L['foot_why']}</div>
  </td></tr>

</table>
</td></tr></table>
</body></html>"""

# ---------------- MailerLite API (uus API: connect.mailerlite.com) ----------------

def _plain(s):
    return (s.replace("&ndash;","–").replace("&mdash;","—").replace("&middot;","·"))

def _ml_post(url, token, payload):
    data=json.dumps(payload).encode("utf-8")
    req=urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", "Bearer "+token)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def send_campaign(lang, html_content, cfg, token, ws, we, dry_run=False):
    L=I18N[lang]
    rng=_plain(daterange(ws,we,L))
    subj_tmpl=(cfg.get("subject") or {}).get(lang) or _plain(L["subject"])
    subject=subj_tmpl.replace("{range}", rng)
    seg=(cfg.get("segments") or {}).get(lang)
    grp=(cfg.get("groups") or {}).get(lang)
    def _bad(v): return (not v) or (isinstance(v,str) and v.startswith("REPLACE"))
    if _bad(seg) and _bad(grp):
        raise RuntimeError(f"[{lang}] pole segmenti ega gruppi konfiguratsioonis (loo MailerLite'is, tuvasta keel={lang}, ja pane ID mailerlite_config.json-i).")
    email={
        "subject": subject,
        "from_name": cfg.get("from_name","skene.info"),
        "from": cfg["from_email"],
        "content": html_content,
    }
    payload={"name": f"skene.info nadalakiri {rng} [{lang}]", "type":"regular", "emails":[email]}
    if not _bad(seg): payload["segments"]=[seg]
    else: payload["groups"]=[grp]
    api=cfg.get("api_base","https://connect.mailerlite.com/api")
    tgt = f"segment {seg}" if not _bad(seg) else f"group {grp}"
    if dry_run:
        print(f"  [DRY-RUN {lang}] looks kampaania -> {tgt}; subjekt: {subject!r}; from {email['from']}")
        return None
    created=_ml_post(f"{api}/campaigns", token, payload)
    cid=(created.get("data") or {}).get("id")
    if not cid:
        raise RuntimeError(f"[{lang}] kampaania loomine ebaonnestus: {created}")
    _ml_post(f"{api}/campaigns/{cid}/schedule", token, {"delivery":"instant"})
    print(f"  [SENT {lang}] kampaania {cid} -> {tgt}; subjekt: {subject!r}")
    return cid

def load_token(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True, help="baasnimi; toodab <out>.et.html ja <out>.en.html")
    ap.add_argument("--date", default=None)
    ap.add_argument("--send", action="store_true", help="saada MailerLite'i API kaudu (muidu ainult failid)")
    ap.add_argument("--dry-run", action="store_true", help="--send-iga: naita mida saadaks, aga ara saada")
    ap.add_argument("--token-file", default="mailerlite_token.txt")
    ap.add_argument("--config", default="mailerlite_config.json")
    args=ap.parse_args()

    ref=parse_d(args.date) if args.date else dt.date.today()
    ws,we=this_and_next_week(ref)

    with open(args.data, encoding="utf-8") as f:
        data=json.load(f)
    entries=data.get("entries",[])
    sel=[e for e in entries if e.get("c") in EESTI and in_window(e,ws,we)]
    sel.sort(key=lambda e:(e["d"], e.get("t","")))

    base=args.out[:-5] if args.out.endswith(".html") else args.out
    outputs={}
    for lang in ("et","en"):
        htmlout=build_html(sel, ws, we, lang)
        path=f"{base}.{lang}.html"
        with open(path,"w",encoding="utf-8") as f:
            f.write(htmlout)
        outputs[lang]=htmlout
        print(f"OK: {path}  ({len(sel)} kirjet; aken {ws}..{we})")
    for e in sel:
        print("  -", e["d"], e.get("t"), "|", e.get("n","")[:50])

    if args.send:
        token=load_token(args.token_file)
        with open(args.config, encoding="utf-8") as f:
            cfg=json.load(f)
        print("Saatmine (MailerLite API)%s:" % (" [DRY-RUN]" if args.dry_run else ""))
        for lang in ("et","en"):
            try:
                send_campaign(lang, outputs[lang], cfg, token, ws, we, dry_run=args.dry_run)
            except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError) as ex:
                print(f"  [VIGA {lang}] {ex}", file=sys.stderr)

if __name__=="__main__":
    main()
