import json
T = '2026-11-22'
def load(p): return json.load(open(p, encoding='utf-8'))
def save(p, d): json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
www = load('data/manual.json'); klubi = load('klubi/data/manual.json')

# 1) Jimi Hendrix 84 x3 (www, rock+bluus; precedent CryBaby 10.10/31.10)
H = {'praegu': 'eelmüük 20 € (BEBOP, piiratud) / 25 € (SWING) / 30 € (COOL JAZZ), soodus 20 €; kohapeal 35 € / soodus 25 €; toetajapilet 50 €',
     'allikas': 'Piletikeskus + FB event, kontrollitud 22.11.2026'}
for d, rn, kl, fbid, pk in [
    ('2026-11-26', 'I', 'bc6cd501-d538-4ba7-93f6-da044abf36da', '2184827645439332', '7nhiuj'),
    ('2026-11-27', 'II', 'c005a9ac-fa80-4bbf-9200-0956b830cf5d', '1167064192584675', '6v12qh'),
    ('2026-11-28', 'III', 'fc55c82b-8f86-4762-b631-ade8dac54eb9', '1102718975805273', 'g4sqqa')]:
    www.append({
        'd': d, 't': 'kontsert',
        'n': 'Jimi Hendrix 84 %s kontsert: Ukaredad, Vaiglad, Lillepea' % rn,
        'a': 'algus 21.00; Hendrixi-kava: Raul Ukareda, Raul Vaigla, Andrus Lillepea + erikülalised Carlos Ukareda ja Marie Vaigla',
        'b': ['Raul Ukareda', 'Raul Vaigla', 'Andrus Lillepea', 'Carlos Ukareda', 'Marie Vaigla'],
        'v': "Philly Joe's", 'c': 'Tallinn', 'g': ['rock', 'bluus'],
        'sn': 'kluub.ee', 'su': 'https://www.kluub.ee/et/events/tallinn/' + kl,
        'on_': 'Facebook event', 'ou': 'https://www.facebook.com/events/%s' % fbid,
        'pu': 'https://piletikeskus.ee/et/e/' + pk, 'hind': H,
        'lisatud': T,
        'nb': 'lisatud postkastijooksus 22.11.2026 (samm 2c). Allikad: kluub.ee + FB event + Piletikeskus (kuupäev/kellaaeg kontrollitud piletilehelt). Bluusrokk-Hendrixi-kava; pretsedent: Jimi Hendrix 84 — CryBaby 10.10 / 31.10 (rock+bluus).'})

# 2) Baile do Lainão - The BreakOut (klubi, baile funk; precedent vol IV 04.09)
klubi.append({
    'd': '2026-11-27', 't': 'klubi', 'n': 'Baile do Lainão — The BreakOut',
    'a': '22.00-03.00; Brazilian funk, mega house, funk eletrônico, baile edits',
    'b': ['DJ Yungï (BRA)', 'El Kajakas (GUA)', 'shbxsz (IND)'],
    'v': 'Uus Laine', 'c': 'Tallinn', 'g': ['baile funk', 'house'],
    'sn': 'kluub.ee', 'su': 'https://www.kluub.ee/et/events/tallinn/2199829a-087a-4737-9608-2d96193946a9',
    'on_': 'Facebook event', 'ou': 'https://www.facebook.com/events/2129740374388798',
    'hind': {'praegu': 'tasuta', 'allikas': 'FB event (kluub.ee), kontrollitud 22.11.2026'},
    'lisatud': T,
    'nb': 'lisatud postkastijooksus 22.11.2026 (samm 2c). Allikad: kluub.ee + FB event (Uus Laine, R 27.11 kell 22). Žanr ürituse enda tekstist; sari varem klubi-saidil (Baile do Lainão vol IV 04.09).'})

# 3) Likane Leppäne enrich hind
for e in www:
    if e.get('n', '').startswith('Likane Leppäne') and not e.get('hind'):
        e['hind'] = {'praegu': '5 / 8 €', 'mark': 'uksel', 'allikas': 'FB event (kluub.ee peegel), kontrollitud 22.11.2026'}
        e['nb'] = e.get('nb', '') + ' Rikastatud 22.11.2026: hind FB eventist; koht kannab nüüd nime Anemon12 (Ülase tn 12).'

save('data/manual.json', www); save('klubi/data/manual.json', klubi)

# 4) Bandcamp ack (Rein Fuks pending Silver's decision; tracked in otsused.json)
s = load('data/bandcamp_seen.json')
u = 'https://seksound.bandcamp.com/album/ma-tegin-ju-nalja'
if u not in s['seen']:
    s['seen'].append(u)
json.dump(s, open('data/bandcamp_seen.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', len(www), len(klubi))
