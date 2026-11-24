import json
from datetime import date, timedelta
T = date(2026, 11, 20)
def L(p):
    d = json.load(open(p, encoding='utf-8'))
    return d if isinstance(d, list) else d.get('entries', d.get('events', []))
def dt(s):
    try: return date.fromisoformat(str(s)[:10])
    except Exception: return None
def line(e):
    d = dt(e['d'])
    v = e.get('v', '')
    loc = e.get('linn') or (e.get('c') if e.get('c') not in ('Tallinn', 'mujal', None) else '')
    s = f"{d.strftime('%d.%m')} {e['n']} - {v}" + (f", {loc}" if loc and loc not in v else '')
    h = e.get('hind', {})
    if isinstance(h, dict) and h.get('praegu'): s += f" ({h['praegu']})"
    if e.get('lisatud') == T.isoformat(): s = f"**{d.strftime('%d.%m')} UUS! " + s[6:] + '**'
    return s
def section(p, root):
    ev = [e for e in L(p) if isinstance(e, dict) and dt(e.get('d')) and not e.get('rel') and e.get('t') not in ('reliis', 'merch')
          and e.get('c') not in ('Euroopa', 'LÃ¤ti', 'Leedu', 'Soome', 'Rootsi', 'Norra', 'Saksamaa') and e.get('v') != 'tuur' or (isinstance(e, dict) and e.get('v') == 'tuur' and e.get('c') == 'mujal' and not e.get('rel'))]
    ev = [e for e in ev if dt(e.get('d')) and e.get('c') != 'Euroopa']
    ev.sort(key=lambda e: (e['d'], e['n']))
    out = []
    def blk(title, a, b):
        xs = [line(e) for e in ev if a <= dt(e['d']) <= b]
        if xs: out.append(title + '\n\n' + '\n'.join(xs))
    blk('Sel nÃ¤dalavahetusel:', T, T + timedelta(days=2))
    blk('JÃ¤rgmisel nÃ¤dalal:', T + timedelta(days=3), T + timedelta(days=9))
    blk('Pilk ette:', T + timedelta(days=10), T + timedelta(days=16))
    rel = [e for e in L(p) if isinstance(e, dict) and e.get('rel') and (dt(e.get('lisatud')) or T) >= T - timedelta(days=7)]
    if rel:
        out.append('VÃ¤rsked reliisid:\n\n' + '\n'.join(('UUS! ' if e.get('lisatud') == T.isoformat() else '') + f"{e['n']} ({e.get('ou') or e.get('su')})" for e in rel))
    out.append('KÃµik Ã¼ritused ja piletid: ' + root)
    return '\n\n'.join(out)
w = section('data/data.json', 'www.skene.info')
r = section('rap/data/data.json', 'rap.skene.info')
k = section('klubi/data/data.json', 'klubi.skene.info')
cnt = lambda p: sum(1 for e in L(p) if isinstance(e, dict) and e.get('lisatud') == T.isoformat())
txt = f"""# NÃ¤dalapostitus - reede, 20.11.2026

**Kanal:** FB Page + IG @skene.info; nÃ¤dalapildid lÃ¤hevad IG-sse Make.com kaudu karussellina (**R 11:45**)
**Staatus:** MUSTAND - Silver kinnitab ja postitab
**Uusi kirjeid selles sweepis:** www 17 / rap 5 / klubi 10

---

## Postituse tekst (metal / skene.info)

SEL NÃ„DALAL & TULEKUL - 20.11

{w}

---

## RÃ¤pi-sektsioon (rap.skene.info)

{r}

---

## Klubi-sektsioon (klubi.skene.info)

{k}
"""
open('postitused/2026-11-20-tulekul.md', 'w', encoding='utf-8').write(txt)
print(txt[:1800])

