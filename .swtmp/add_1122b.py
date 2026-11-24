import json
T = '2026-11-22'
SV = 'Silveri otsus 22.11.2026 (vastus vestluses).'
def load(p): return json.load(open(p, encoding='utf-8'))
def save(p, d): json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
www = load('data/manual.json'); klubi = load('klubi/data/manual.json')

www.append({
    'd': '2026-11-25', 't': 'reliis', 'rel': 1, 'n': 'Rein Fuks - «Ma tegin ju nalja»',
    'a': 'Album, 12 lugu (Seksound SEKs100). Rein Fuks: muusika, sõnad, kõik pillid, salvestus ja miks; külalisvokaal Kristel Eplik (2 lugu); master Lauri Liivak. Vinüül 100 tk (saadetakse ~15.12)',
    'b': ['Rein Fuks'], 'g': ['indie', 'shoegaze', 'rock'],
    'sn': 'Bandcamp', 'su': 'https://seksound.bandcamp.com/album/ma-tegin-ju-nalja',
    'lisatud': T,
    'nb': 'LISATUD 22.11.2026 check_bandcamp.py alerti peale. ' + SV + ' Allikas: labeli enda Bandcampi albumileht ("releases November 25, 2026", datePublished 25 Nov 2026); seksound.com on sama Bandcampi peegel, mitte sõltumatu allikas. Bandcampi sildid: dreampop, indie pop, indie rock, shoegaze. Kuupäev kontrolli üle väljalaskel (REEGLID §6 Bandcampi-lõks).'})

www.append({
    'd': '2026-11-28', 't': 'kontsert', 'n': 'Lasten Hautausmaa Duo (FIN) + Nova Lux + Riste @ Anemon12',
    'a': 'uksed 19.00; 20.00 Riste, 21.00 Lasten Hautausmaa Duo, 22.00 Nova Lux',
    'b': ['Lasten Hautausmaa Duo (FIN)', 'Nova Lux', 'Riste'],
    'v': 'Anemon12', 'c': 'Tallinn', 'g': ['alt', 'rock'],
    'sn': 'kluub.ee', 'su': 'https://www.kluub.ee/et/events/tallinn/9752fe8a-4819-4f24-bb9d-1eb2a86e1914',
    'on_': 'Facebook event', 'ou': 'https://www.facebook.com/events/1627019615418994',
    'hind': {'praegu': '5 / 8 €', 'mark': 'uksel', 'allikas': 'FB event (kluub.ee peegel), kontrollitud 22.11.2026'},
    'lisatud': T,
    'nb': 'lisatud postkastijooksus 22.11.2026 (samm 2c). Allikad: kluub.ee + FB event (Anemon12, Ülase 12). ' + SV + ' Sildid Nova Luxi järgi (Bandcamp: alternative/depressive rock); Lasten Hautausmaa = death pop, Riste = lo-fi tweepop.'})

klubi.append({
    'd': '2026-11-27', 't': 'kontsert', 'n': 'Terminal Live: GØK2 & Luka',
    'a': '21.00-01.00; live: LUKA (elektrooniline popp, glitch) + GØK2 (elektropunk, breakcore, big beat, nu metal)',
    'b': ['GØK2', 'Luka'], 'v': 'Terminal Records&Bar', 'c': 'Tallinn', 'g': ['electro', 'breaks'],
    'sn': 'kluub.ee', 'su': 'https://www.kluub.ee/et/events/tallinn/057f2bc0-510a-4120-9100-83b438bc0d8e',
    'on_': 'Facebook event', 'ou': 'https://www.facebook.com/events/1497648022260429',
    'pu': 'https://fienta.com/et/terminal-live-goek2-luka',
    'hind': {'praegu': 'noortepilet 5 € / varajane 8 € / eelmüük 10 € / kohapeal 15 €', 'allikas': 'Fienta, kontrollitud 22.11.2026'},
    'lisatud': T,
    'nb': 'lisatud postkastijooksus 22.11.2026 (samm 2c). Allikad: kluub.ee + FB event + Fienta (kuupäev/kellaaeg Fientast). ' + SV})

klubi.append({
    'd': '2026-11-27', 't': 'klubi', 'n': 'Bar IDA: Plastik all night long',
    'a': '20.00-04.00; Plastik all night long (+ kiimsask, mrt)',
    'b': ['Plastik', 'kiimsask', 'mrt'], 'v': 'Bar IDA', 'c': 'Tallinn', 'g': ['house'],
    'sn': 'kluub.ee', 'su': 'https://www.kluub.ee/et/events/tallinn/82312157-4930-4ef6-95f6-5cf87715ab5e',
    'on_': 'Facebook event', 'ou': 'https://www.facebook.com/events/2601908953591171',
    'hind': {'praegu': 'tasuta kuni 22.00, hiljem 5 / 7 €', 'allikas': 'FB event (kluub.ee), kontrollitud 22.11.2026'},
    'lisatud': T,
    'nb': 'lisatud postkastijooksus 22.11.2026 (samm 2c). Allikad: kluub.ee + FB event (IDA Radio, Telliskivi 60a). Žanr ürituse tekstis puudub; silt house = ' + SV})

save('data/manual.json', www); save('klubi/data/manual.json', klubi)
print('ok', len(www), len(klubi))
