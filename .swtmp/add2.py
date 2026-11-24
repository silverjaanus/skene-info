import json
T = '2026-11-20'
NB = 'lisatud sweepi ülekontrollis 20.11.2026. '
def fb(i): return 'https://www.facebook.com/events/%s/' % i
def load(p): return json.load(open(p, encoding='utf-8'))
def save(p, d): json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
www = load('data/manual.json'); rap = load('rap/data/manual.json'); klubi = load('klubi/data/manual.json')
def ev(t, d, n, b, v, c, g, sn, su, ou, on_='Facebook event', a='', pu=None, hind=None, extra=None, nb=''):
    e = {'d': d, 't': t, 'n': n, 'b': b, 'v': v, 'c': c, 'g': g, 'sn': sn, 'su': su, 'on_': on_, 'ou': ou}
    if a: e['a'] = a
    if pu: e['pu'] = pu
    if hind: e['hind'] = hind
    if extra: e.update(extra)
    if not e['ou']: e.pop('ou'); e.pop('on_')
    e['nb'] = NB + nb; e['lisatud'] = T
    return e
H = lambda s: {'praegu': s, 'allikas': 'ürituse leht, kontrollitud 20.11.2026'}
klubi += [
 ev('klubi', '2026-11-21', 'Lights Out @ Fonoteek', ['Funkomatik', 'Olivar', 'Slin Remi'], 'Fonoteek', 'Tallinn', ['house'], 'Fonoteek FB events-tab', 'https://www.facebook.com/fonoteekbar/events', fb('1171299105563740'),
    a='23.00–04.00; house, UK garage; 20+', pu='https://gateme.com/et/fonoteek/104579-lights-out-i-2111-i-fonoteek', hind=H('FB going kuni 00.00 / terve öö 5 € / 7 €, tavapilet 10 €'), nb='Kaks allikat: FB event (Fonoteek + Muusikalinn Tallinn) + GateMe. Sari on klubi-saidil varem olnud (Lights Out 29.08, 19.09, 30.10).'),
 ev('klubi', '2026-11-27', 'Stereo @ Fonoteek', ['MHKL', 'ARU'], 'Fonoteek', 'Tallinn', ['house'], 'Fonoteek FB events-tab', 'https://www.facebook.com/fonoteekbar/events', fb('1191932696509370'),
    a='23.00–04.00; house music all night', pu='https://gateme.com/fonoteek/104567-stereo-2711-fonoteek', nb='Kaks allikat: FB event + GateMe; RA 2585621. Sari varem saidil (25.09, 23.10).'),
 ev('klubi', '2026-11-27', 'Piidivabrik @ Klubi Neli', ['Muudu', 'Kurly Beats', 'Paap', 'Paula', 'Hurmet Ilus'], 'Klubi Neli', 'Tartu', ['house', 'techno'], 'Klubi Neli GateMe', 'https://gateme.com/et/klubineli/', '', on_='',
    a='21.00–05.00; house, breakbeat, afro house, meloodiline techno, deep/progressive house', pu='https://gateme.com/et/klubineli/104582-piidivabrik-i-klubi-neli-i-2711/', hind=H('eelmüük 5 €, hiljem 9 €, Fast Track 15 €'), nb='Piletimüüja leht (REEGLID §3 erand: piletileht piisab) + Klubi Neli GateMe-koondleht; žanrid ürituse kirjeldusest.'),
 ev('klubi', '2026-11-28', 'Äfters @ Klubi Neli', ['QSLAP', '24K (LV)'], 'Klubi Neli', 'Tartu', ['house'], 'Klubi Neli GateMe', 'https://gateme.com/et/klubineli/', '', on_='',
    a='21.00–05.00; QSLAP (Living room, gruuv ja hüpnootilised rütmid), 24K (Club side)', pu='https://gateme.com/et/klubineli/104583-afters-i-klubi-neli-i-2811/', hind=H('21–23 tasuta, 23–01 5 €, 01–05 9 €, Fast Track 15 €'), nb='Piletimüüja leht (REEGLID §3 erand) + Klubi Neli GateMe-koondleht.'),
 ev('klubi', '2026-11-20', '/diːp kʌts/ @ huba.club', ['Kässar', 'Kalju999', 'DJTHZ909'], 'huba.club', 'Tartu', ['house', 'minimal'], 'huba.club FB events-tab', 'https://www.facebook.com/hubbaclubba/events', fb('2038549646838375'),
    a='22.00–02.00; deep house, minimal, tech, bounce', hind=H('5 €'), nb='Kaks allikat: FB event + kluub.ee Tartu (žanr tagurpidi kirjutatud kirjelduses: „deep house minimal tech bounce“).'),
]
rap += [
 ev('kontsert', '2026-12-05', 'PRODIGYBOYS «Moosekandid» albumi esitluskontsert', ['PRODIGYBOYS'], 'D3', 'Tallinn', ['hiphop'], 'D3 kava', 'https://www.d-3.ee/events/', 'https://www.d-3.ee/events/prodigyboys-moosekandid-albumi-esitluskontsert/', on_='D3',
    a='19.00–22.00 esitluskontsert (0+), 23.00–04.00 afterparty (18+)', pu='https://gateme.com/et/D3Tallinn/104540-prodigyboys-moosekandid-albumi-esitluskontsert-i-d3-i-0512/', nb='Kaks allikat: D3 ürituseleht + GateMe. Seotud reliisikirje PRODIGYBOYS «MOOSEKANDID» (28.10).'),
]
www += [
 ev('kontsert', '2027-11-16', 'Paavli.Live: HENGE (UK)', ['Henge (UK)'], 'Paavli Kultuurivabrik', 'Tallinn', ['rock', 'alt'], 'paavli.ee', 'https://paavli.ee/sundmused/', fb('1143644054710623'),
    a='kosmilise progeroki ja elektroonilise muusika kooslus', pu='https://fienta.com/et/paavli-live-henge', nb='Kaks allikat: paavli.ee ürituseleht (https://paavli.ee/sundmused/paavli%e2%80%a4live-henge-uk/) + Fienta. Kuupäev 16.11.2027 lehe tekstist.'),
]
save('data/manual.json', www); save('rap/data/manual.json', rap); save('klubi/data/manual.json', klubi)
# sources.json fixes
s = load('sweep/sources.json')
fix = {'https://www.facebook.com/search/top?q=Contriber%20%26%20Philly%20Joe%27s%20Tartu': 'https://www.facebook.com/contriberphillyjoestartu/events',
       'https://www.facebook.com/search/top?q=Trancedeluxe': 'https://www.facebook.com/profile.php?id=100069001470773&sk=events',
       'https://www.facebook.com/search/top?q=PoCo%20popkunstimuuseum': 'https://www.facebook.com/poco.art.tallinn/events',
       'https://www.facebook.com/search/top?q=Balta%20Chill': 'https://www.facebook.com/profile.php?id=61593493725024&sk=events'}
n = 0
def walk(o):
    global n
    if isinstance(o, dict):
        if o.get('url') in fix:
            o['url'] = fix[o['url']]; o['nb'] = (o.get('nb', '') + ' | URL parandatud 20.11.2026 (FB lehe otsingust).').strip(' |'); n += 1
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(s)
json.dump(s, open('sweep/sources.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('sources fixed', n)
