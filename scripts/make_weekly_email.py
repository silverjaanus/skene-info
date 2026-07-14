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
# kategooria (alamdomeen) varvid + sildid — VARV eristab kategooriat, tuup jaab tekstina
CAT_COLOR={"metal":"#93392C","rap":"#2E5EAA","klubi":"#6E45A8"}
CAT_LABEL={"et":{"metal":"METAL","rap":"RÄPP","klubi":"KLUBI"},"en":{"metal":"METAL","rap":"RAP","klubi":"CLUB"}}
CAT_ORDER=["metal","rap","klubi"]
# MailerLite eelistuste/loobumise link (grupid subscriber-managed); kinnita ML manage-tag
MANAGE_LINK="{$preferences}"
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

def event_row(e, L, lang="et"):
    s,en=event_span(e)
    t=e.get("t","")
    cat=e.get("_cat","metal")
    col=CAT_COLOR.get(cat,HALL)
    label=CAT_LABEL.get(lang,CAT_LABEL["et"]).get(cat,cat.upper())
    typetext=L["type"].get(t,t.upper())
    is_rel = t in ("reliis","merch") or e.get("rel")
    datebig=f"{s.day:02d}.{s.month:02d}"
    if is_rel:
        wl=L["new"]
    else:
        wl=L["wday"][s.weekday()]
        if e.get("d2"): wl+=f"&ndash;{en.day:02d}.{en.month:02d}"
    tag=(f'<span style="display:inline-block;background:{col};color:#FFFFFF;'
         f'font:700 11px/1.4 \'Courier New\',monospace;letter-spacing:.5px;'
         f'padding:2px 7px;">{label}</span>'
         f'<span style="font:400 11px/1.4 \'Courier New\',monospace;color:{HALL};'
         f'margin-left:8px;text-transform:uppercase;letter-spacing:.4px;">{typetext}</span>')
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

def build_html(entries, ws, we, lang, cats):
    L=I18N[lang]
    rows="".join(event_row(e, L, lang) for e in entries)
    n=len(entries); krje=L["entry_1"] if n==1 else L["entry_n"]
    rng=daterange(ws,we,L)
    missing=[c for c in CAT_ORDER if c not in cats]
    promo_html=""
    if missing:
        CL=CAT_LABEL.get(lang,CAT_LABEL["et"])
        have_txt=", ".join(CL[c] for c in cats if c in CL)
        miss_txt=", ".join(CL[c] for c in missing)
        if lang=="et":
            ph="Telli juurde teisi teemasid"
            pb=(f"Sinu kirjas on praegu <b>{have_txt}</b>. Saad juurde tellida <b>{miss_txt}</b> "
                f"&mdash; kõik tuleb ühes kirjas nädalas, iga teema saab eraldi välja lülitada.")
            pbtn="Halda eelistusi &rarr;"
        else:
            ph="Add more topics"
            pb=(f"Right now your email covers <b>{have_txt}</b>. You can add <b>{miss_txt}</b> "
                f"&mdash; everything arrives in one weekly email and each topic can be switched off.")
            pbtn="Manage preferences &rarr;"
        promo_html=f"""  <!-- lisa-teemade plokk (dunaamiline: naitab puuduvaid kategooriaid) -->
  <tr><td style="padding:8px 28px 22px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PABER};border:1px dashed {JOON};">
      <tr><td style="padding:16px 18px;">
        <div style="font:700 14px/1.4 Arial,Helvetica,sans-serif;color:{TINT};">{ph}</div>
        <div style="font:400 13px/1.5 Arial,Helvetica,sans-serif;color:{HALL};margin:4px 0 12px;">{pb}</div>
        <a href="{MANAGE_LINK}" style="display:inline-block;background:{TINT};color:{PABER};font:700 13px/1 Arial,Helvetica,sans-serif;text-decoration:none;padding:11px 18px;">{pbtn}</a>
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
      <a href="{MANAGE_LINK}" style="color:{PABER};">{L['foot_prefs']}</a> &nbsp;·&nbsp;
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

def load_sources(repo, ws, we):
    srcs={"metal":os.path.join(repo,"data","data.json"),
          "rap":os.path.join(repo,"rap","data","data.json"),
          "klubi":os.path.join(repo,"klubi","data","data.json")}
    out=[]
    for cat,path in srcs.items():
        if not os.path.exists(path): continue
        data=json.load(open(path, encoding="utf-8"))
        for e in data.get("entries",[]):
            if e.get("c") in EESTI and in_window(e,ws,we):
                ee=dict(e); ee["_cat"]=cat; out.append(ee)
    return out

def gen_combo(all_ev, cats, ws, we, base):
    sel=[e for e in all_ev if e.get("_cat") in cats]
    sel.sort(key=lambda e:(e["d"], CAT_ORDER.index(e.get("_cat","metal")), e.get("t","")))
    tag="+".join(cats)
    outs={}
    for lang in ("et","en"):
        h=build_html(sel, ws, we, lang, cats)
        path=f"{base}-{tag}.{lang}.html"
        with open(path,"w",encoding="utf-8") as f:
            f.write(h)
        outs[lang]=h
        print(f"OK {path}  ({len(sel)} kirjet; kategooriad {tag})")
    return outs

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo", help="repo juur (loeb data/, rap/data/, klubi/data/)")
    ap.add_argument("--data", help="(vana teekond) uks metal data.json")
    ap.add_argument("--cats", help="komadega kategooriad kirja, nt metal,klubi; vaikimisi naidiskombod")
    ap.add_argument("--out", required=True, help="baasnimi; toodab <out>-<kombo>.et/.en.html")
    ap.add_argument("--date", default=None)
    ap.add_argument("--config", default="mailerlite_config.json")
    args=ap.parse_args()

    global MANAGE_LINK
    if os.path.exists(args.config):
        try:
            MANAGE_LINK=json.load(open(args.config, encoding="utf-8")).get("manage_link", MANAGE_LINK)
        except Exception:
            pass

    ref=parse_d(args.date) if args.date else dt.date.today()
    ws,we=this_and_next_week(ref)

    if args.repo:
        all_ev=load_sources(args.repo, ws, we)
    elif args.data:
        data=json.load(open(args.data, encoding="utf-8"))
        all_ev=[dict(e, _cat="metal") for e in data.get("entries",[])
                if e.get("c") in EESTI and in_window(e,ws,we)]
    else:
        raise SystemExit("Anna --repo (soovitatav) voi --data")

    base=args.out[:-5] if args.out.endswith(".html") else args.out
    if args.cats:
        combos=[[c.strip() for c in args.cats.split(",") if c.strip() in CAT_ORDER]]
    else:
        combos=[["metal"],["rap"],["klubi"],["metal","rap","klubi"]]
    for cats in combos:
        if cats: gen_combo(all_ev, cats, ws, we, base)
    print("MARKUS: kombinatsioonisaatmine kaib bucket-gruppidega (eraldi samm, ainult Silveri kasul).")

if __name__=="__main__":
    main()
