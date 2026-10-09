#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ig_mainimised.py -- uued IG kommentaarid, märkimised ja DM-id -> Telegrami kokkuvõte.

Jookseb GitHub Actionsis (.github/workflows/ig_mainimised.yml) 2x päevas.
Allikad (graph.instagram.com, IG_TOKEN):
  - kommentaarid meie viimastele postitustele
  - postitused, kus @skene.info on märgitud (/me/tags)
  - DM-id ja story-mainimised (/me/conversations)
Vastuse mustandid teeb GitHub Models (GITHUB_TOKEN, models: read); kui see ei tööta,
tuleb kokkuvõte ilma mustanditeta. Midagi ise ei postitata.

NB: repo ja Actionsi logid on AVALIKUD -> logisse ainult arvud, mitte sisu.
Seis (ainult nähtud ID-d) failis ig/mainimised_seis.json.
"""
import datetime as dt, html, json, os, sys, urllib.parse, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH = "https://graph.instagram.com/v23.0"
SEIS = os.path.join(ROOT, "ig", "mainimised_seis.json")
MEIE = "skene.info"


def get(path, **params):
    params["access_token"] = os.environ["IG_TOKEN"]
    url = f"{GRAPH}/{path}?{urllib.parse.urlencode(params)}"
    try:
        return json.loads(urllib.request.urlopen(url, timeout=60).read())
    except urllib.error.HTTPError as e:
        print(f"  {path.split('/')[0]}: HTTP {e.code} (jätan vahele)")
        return {}


def parse_ts(s):
    try:
        return dt.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def koguda(seen, cutoff):
    uued = []

    def lisa(kid, ts, **kw):
        t = parse_ts(ts or "")
        if kid in seen or (t and t < cutoff):
            seen.add(kid)
            return
        seen.add(kid)
        uued.append(dict(id=kid, ts=ts, **kw))

    # 1) kommentaarid meie postitustele
    media = get("me/media", fields="id,permalink,caption,comments_count,timestamp", limit=25).get("data", [])
    for m in media:
        if not m.get("comments_count"):
            continue
        for c in get(f"{m['id']}/comments", fields="id,text,username,timestamp", limit=50).get("data", []):
            if c.get("username") == MEIE:
                continue
            lisa("c" + c["id"], c.get("timestamp"), tyyp="kommentaar", kes=c.get("username", "?"),
                 tekst=c.get("text", ""), link=m.get("permalink"),
                 kontekst=(m.get("caption") or "")[:120])

    # 2) postitused, kus meid on märgitud
    for t in get("me/tags", fields="id,caption,permalink,username,timestamp", limit=25).get("data", []):
        lisa("t" + t["id"], t.get("timestamp"), tyyp="märkimine", kes=t.get("username", "?"),
             tekst=(t.get("caption") or "")[:400], link=t.get("permalink"), kontekst="")

    # 3) DM-id ja story-mainimised
    conv = get("me/conversations", platform="instagram",
               fields="id,updated_time,messages.limit(5){id,from,message,created_time,story}", limit=20)
    for cv in conv.get("data", []):
        for msg in (cv.get("messages") or {}).get("data", []):
            frm = (msg.get("from") or {}).get("username", "?")
            if frm == MEIE:
                continue
            story = msg.get("story") or {}
            on_mainimine = "mention" in story
            lisa("d" + msg["id"], msg.get("created_time"),
                 tyyp="story-mainimine" if on_mainimine else "DM", kes=frm,
                 tekst=msg.get("message") or ("(mainis sind oma story's)" if on_mainimine else "(meedia)"),
                 link=(story.get("mention") or {}).get("link") or "https://www.instagram.com/direct/inbox/",
                 kontekst="")
    return uued


def mustandid(uued):
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok or not uued:
        return {}
    items = [{"i": i, "tyyp": u["tyyp"], "kes": u["kes"], "tekst": u["tekst"][:500],
              "postituse_tekst": u.get("kontekst", "")} for i, u in enumerate(uued)]
    prompt = (
        "Oled skene.info Instagrami konto haldur. skene.info on Eesti metal-, räpi- ja klubiürituste "
        "kalender (skene.info, iganädalane uudiskiri skene.info/liitu). Kirjuta igale sissetulnud "
        "kommentaarile, märkimisele või sõnumile lühike vastuse mustand korrektses, loomulikus eesti keeles "
        "(kui sõnum on inglise keeles, siis inglise keeles). Toon: sõbralik, asjalik, mitte turunduslik, "
        "max 1–2 lauset, emoji maksimaalselt üks. Ära luba midagi, mida skene.info ei tee (ei müü pileteid). "
        "Kui vastust pole vaja (nt spämm või ainult emoji), pane mustandiks tühi string.\n"
        'Vasta AINULT JSON-iga kujul {"vastused":[{"i":0,"mustand":"..."}]}.\n\n'
        + json.dumps(items, ensure_ascii=False))
    body = json.dumps({"model": "openai/gpt-4.1-mini", "temperature": 0.4,
                       "response_format": {"type": "json_object"},
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://models.github.ai/inference/chat/completions", data=body,
                                 headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=90).read())
        d = json.loads(r["choices"][0]["message"]["content"])
        return {int(x["i"]): x.get("mustand", "") for x in d.get("vastused", [])}
    except Exception as e:
        print(f"  mustandid ei õnnestunud: {type(e).__name__}")
        return {}


def telegram(tekst):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat = os.environ.get("TELEGRAM_CHAT_ID") or "1810496014"
    data = urllib.parse.urlencode({"chat_id": chat, "text": tekst, "parse_mode": "HTML",
                                   "disable_web_page_preview": "true"}).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=30)


IKOON = {"kommentaar": "💬", "märkimine": "🏷", "DM": "✉️", "story-mainimine": "📣"}


def main():
    if not os.environ.get("IG_TOKEN"):
        sys.exit("IG_TOKEN puudub")
    seis = json.load(open(SEIS, encoding="utf-8")) if os.path.exists(SEIS) else {}
    esimene = not seis
    seen = set(seis.get("seen", []))
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7 if esimene else 30)

    uued = koguda(seen, cutoff)
    uued.sort(key=lambda u: u.get("ts") or "")
    print(f"Uusi: {len(uued)} (" + ", ".join(f"{k} {sum(u['tyyp'] == k for u in uued)}" for k in IKOON) + ")")

    if uued:
        mu = mustandid(uued)
        osad = [f"<b>skene.info IG: {len(uued)} uut</b>" + (" (viimased 7 päeva)" if esimene else "")]
        for i, u in enumerate(uued):
            rida = (f"{IKOON.get(u['tyyp'], '•')} <b>@{html.escape(u['kes'])}</b> ({u['tyyp']})\n"
                    f"{html.escape(u['tekst'][:300])}")
            if u.get("link"):
                rida += f"\n<a href=\"{html.escape(u['link'])}\">Ava</a>"
            if mu.get(i):
                rida += f"\n➡️ <i>{html.escape(mu[i])}</i>"
            osad.append(rida)
        # Telegrami piir 4096 märki -> saada tükkidena
        tykk = ""
        for o in osad:
            if len(tykk) + len(o) > 3800:
                telegram(tykk)
                tykk = ""
            tykk += o + "\n\n"
        if tykk:
            telegram(tykk)
        print("Telegrami saadetud")

    seis = {"seen": sorted(seen)[-3000:], "viimati": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    with open(SEIS, "w", encoding="utf-8") as f:
        json.dump(seis, f, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
