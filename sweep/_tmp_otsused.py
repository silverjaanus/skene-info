# -*- coding: utf-8 -*-
"""Silveri otsused 28.08.2026: 3 valjajattu + pick jaab tuhjaks (mehhanism alles)."""
import json, io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(p):
    return json.load(io.open(os.path.join(ROOT, p), encoding='utf-8'))

def save(p, d):
    io.open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(
        json.dumps(d, ensure_ascii=False, indent=1) + '\n')

def lisa(fail, kirjed):
    b = load(fail)
    on = {(str(x.get('d', '')), str(x.get('n', ''))) for x in b}
    n = 0
    for k in kirjed:
        if (k['d'], k['n']) in on:
            continue
        b.append(k)
        n += 1
    save(fail, b)
    print(fail, '+' + str(n), '->', len(b))

lisa('rap/data/blocklist.json', [
 {"d": "2026-09-17", "n": "MORGENSHTERN @ TALLINN",
  "nb": "SKOOBIVALJAJATT 28.08.2026 (Silveri otsus: „MORGENSHTERN valja\"). Venekeelne peavoolu-rapp "
        "Helitehases (korraldaja Ready Events). Baaszanr on hip-hop ja valisartist Eestis laheb reeglina "
        "sisse (Bali Baby / MOMENT 3.0, 27.08), aga peavoolu-valjajatt (Splin, Kaarija) voidab: artist ei "
        "ole Eesti stseeni osa. Blokk hoiab ara, et jargmine sweep uritust uuesti sisse toob. "
        "Allikas: https://helitehas.ee/ + https://www.facebook.com/helitehas/events"},
])

lisa('klubi/data/blocklist.json', [
 {"d": "2026-09-04", "n": "I TRANCE YOU presents ARMIN VAN BUUREN UNOFFICIAL PRE-PARTY",
  "nb": "SKOOBIVALJAJATT 28.08.2026 (Silveri otsus: „Armin van Buureni umber tekkinud peod - valja\"). "
        "Fort Bar, artist Airborn. Trance on klubi zanrinimekirjas, aga AvB-telg on peavoolu-EDM "
        "(REEGLID p1). Allikas: https://ra.co/events/2519035"},
 {"d": "2026-09-05", "n": "Armin van Buuren official afterparty @Balta Hoov",
  "nb": "SKOOBIVALJAJATT 28.08.2026 (Silveri otsus, sama punkt). Korraldaja D3, Balti Jaama Turu hoov. "
        "Allikas: https://www.facebook.com/events/1062776913387493/"},
 {"d": "2026-08-29", "n": "Hot n' Handsome @Wunderbaar",
  "nb": "VALJAJATT 28.08.2026 (Silveri otsus: „Wunderbaar (Parnu) DJ-ohtud valja\"). Wunderbaari FB "
        "events-tab annab ainult nime ja kellaaja, zanri ei ole - 22.08 otsus „kureeritult iga ohtu "
        "eraldi\" ei ole ilma zanriinfota taidetav. Uldreegel: Wunderbaari zanrita DJ-ohtud jaavad "
        "vaikimisi valja, kuni Wunderbaar ise zanri kirjutab. "
        "Allikas: https://www.facebook.com/profile.php?id=100078685784402&sk=events"},
 {"d": "2026-09-04", "n": "Doktor Diisel @Wunderbaar",
  "nb": "VALJAJATT 28.08.2026 (Silveri otsus, sama punkt: Wunderbaari zanrita DJ-ohtud)."},
 {"d": "2026-09-11", "n": "Andres Uibo @Wunderbaar",
  "nb": "VALJAJATT 28.08.2026 (Silveri otsus, sama punkt: Wunderbaari zanrita DJ-ohtud)."},
 {"d": "2026-09-18", "n": "SILK-IN @Wunderbaar",
  "nb": "VALJAJATT 28.08.2026 (Silveri otsus, sama punkt: Wunderbaari zanrita DJ-ohtud)."},
])

# --- sources.json: nb Wunderbaari kirjetele ---
sp = os.path.join(ROOT, 'sweep', 'sources.json')
s = json.load(io.open(sp, encoding='utf-8'))
MARK = (" | 28.08.2026 SILVERI OTSUS: Wunderbaari zanrita DJ-ohtud (Hot n' Handsome, Doktor Diisel, "
        "Andres Uibo, SILK-IN) jaavad VAIKIMISI VALJA - FB events-tab annab ainult nime ja kella. "
        "22.08 otsus „kureeritult iga ohtu eraldi\" kehtib edasi, aga eeldab, et zanr on kuskilt "
        "loetav; kui Wunderbaar zanri kirjutab, vaata uuesti. Kontsertkirjed (nt KURIKS 12.09) ei ole "
        "sellest puudutatud.")
muudetud = 0
def kaia(o):
    global muudetud
    if isinstance(o, dict):
        if 'url' in o and 'wunderbaar' in str(o.get('nimi', '')).lower() + str(o.get('url', '')).lower():
            if 'SILVERI OTSUS: Wunderbaari zanrita' not in str(o.get('nb', '')):
                o['nb'] = str(o.get('nb', '')) + MARK
                muudetud += 1
        else:
            for v in o.values():
                kaia(v)
    elif isinstance(o, list):
        for v in o:
            kaia(v)
kaia(s)
io.open(sp, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1) + '\n')
print('sources.json Wunderbaari kirjeid margitud:', muudetud)
