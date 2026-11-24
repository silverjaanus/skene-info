import json
T = '2026-11-20'
NB = 'lisatud sweepis 20.11.2026. '
def fb(i): return 'https://www.facebook.com/events/%s/' % i
def load(p): return json.load(open(p, encoding='utf-8'))
def save(p, d): json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

www = load('data/manual.json'); rap = load('rap/data/manual.json'); klubi = load('klubi/data/manual.json')
arc = load('data/archive/2026.json')
arcl = arc if isinstance(arc, list) else [x for v in arc.values() if isinstance(v, list) for x in v if isinstance(x, dict)]
rootsg = next((e.get('g') for e in arcl if 'Andres Roots: 30 aastat' in e.get('n', '')), ['bluus'])
print('roots g', rootsg)

def ev(d, n, b, v, c, g, sn, su, ou, a='', pu=None, hind=None, extra=None, nb=''):
    e = {'d': d, 't': 'kontsert', 'n': n, 'b': b, 'v': v, 'c': c, 'g': g, 'sn': sn, 'su': su, 'on_': 'Facebook event', 'ou': ou}
    if a: e['a'] = a
    if pu: e['pu'] = pu
    if hind: e['hind'] = hind
    e['nb'] = NB + nb
    e['lisatud'] = T
    if extra: e.update(extra)
    return e

def rel(d, n, b, g, url, a, nb):
    return {'d': d, 't': 'reliis', 'rel': 1, 'n': n, 'a': a, 'b': b, 'g': g, 'sn': 'Bandcamp (Eesti tag-otsing)', 'su': url, 'on_': 'Bandcamp', 'ou': url, 'lisatud': T, 'nb': NB + nb}

new_www = [
 ev('2027-06-06', 'DORO', ['Doro'], 'Helitehas', 'Tallinn', ['heavy', 'metal'], 'Rada7.ee FB events-tab', 'https://www.facebook.com/helitehas/events', fb('1080037155063845'),
    a='algus 20.00; Doro Peschi (Warlock) esimene kontsert Eestis', nb='Kaks allikat: FB event (ArtEvent + Helitehas) + Rada7.ee ja Helitehase FB events-tab. Piletilinki event-lehe kirjelduses ei olnud, Piletilevi otsing 20.11 ei leidnud.'),
 ev('2026-12-16', 'Andres Roots & Louie Digman @ Salong', ['Andres Roots', 'Louie Digman'], 'Kultuuriklubi Salong', 'Tartu', rootsg, 'Kultuuriklubi Salong FB events-tab', 'https://www.facebook.com/kultuuriklubisalong/events', fb('1105196728797899'),
    a='algus 18.00; slaidkitarr + klaver/vokaal, nelja õhtu „üldsemittejõulutuur“', nb='Kaks allikat: FB event (Andres Roots, Louie Digman + maja) + Salongi FB events-tab. Tuuri teised kuupäevad eraldi kirjetena (Viljandi 17.12, Valga 18.12, Kidrakuur 19.12).'),
 ev('2026-12-17', 'Andres Roots & Louie Digman @ Konservatoorium', ['Andres Roots', 'Louie Digman'], 'Konservatoorium', 'Viljandi', rootsg, 'Konservatoorium FB events-tab', 'https://www.facebook.com/konservatoorium/events', fb('1391669420701934'),
    a='algus 20.00', nb='Kaks allikat: FB event + Konservatooriumi FB events-tab.'),
 ev('2026-12-18', 'Andres Roots & Louie Digman @ Valga Rockiklubi', ['Andres Roots', 'Louie Digman'], 'Valga Rockiklubi', 'Valga', rootsg, 'Rada7.ee FB events-tab', 'https://www.facebook.com/rada7.ee/events', fb('1157649303512026'),
    a='algus 20.00', nb='Kaks allikat: FB event (Andres Roots + Valga Rockiklubi) + Rada7 FB events-tab.'),
 ev('2026-12-19', 'Andres Roots & Louie Digman @ Kidrakuur', ['Andres Roots', 'Louie Digman'], 'Kidrakuur Kultuuriklubi', 'Tallinn', rootsg, 'Kidrakuur FB events-tab', 'https://www.facebook.com/KidrakuurKultuuriklubi/events', fb('1423297816173491'),
    a='algus 21.00', nb='Kaks allikat: FB event + Kidrakuuri FB events-tab.'),
 ev('2026-12-11', 'Jõulupidu: Teravmoon @ Kidrakuur', ['Teravmoon'], 'Kidrakuur Kultuuriklubi', 'Tallinn', ['rock'], 'Kidrakuur FB events-tab', 'https://www.facebook.com/KidrakuurKultuuriklubi/events', fb('1159653486949117'),
    a='uksed 20.00; kaks setti 21.30 ja 22.45', pu='https://sviby.com/et/e/8zvc2p', nb='Kaks allikat: FB event (Kidrakuur + Teravmoon) + Sviby piletileht.'),
 ev('2026-12-12', 'Juudase öö: Mandarones + Kaibald', ['Mandarones', 'Kaibald'], 'Pubi Juudas', 'Tõrva', ['rock', 'stoner'], 'Pubi Juudas FB events-tab', 'https://www.facebook.com/pubijuudas/events', fb('1122366903993551'),
    a='uksed 20.00, Mandarones 21.00, Kaibald 22.00, edasi jämm; kõrbelik filmimuusika, progerock, 70ndad', pu='https://gateme.com/et/pubijuudas/104551-juudase-oo', nb='Kaks allikat: FB event + GateMe piletileht.'),
 ev('2026-12-19', 'Sünge Sünkar 32: The Belka / Mai Skizo / Kuriks', ['The Belka', 'Mai Skizo', 'Kuriks'], 'Kultuuriklubi Tempel', 'Pärnu', ['rock', 'alt'], 'Mai Skizo FB events-tab', 'https://www.facebook.com/MaiSkizo/events', fb('3041820366155000'),
    a='algus 21.00; The Belka 32. sünnipäev, grunge', pu='https://sviby.com/et/e/2e5wuj', nb='Kaks allikat: FB event (Tempel, Kuriks jt) + Sviby piletileht.'),
 ev('2026-12-05', 'Tallinn Indie Shuffle: Around The Sun, Blix, Beid, Muster', ['Muster', 'Beid', 'Around The Sun', 'Blix'], 'Privé Live Club', 'Tallinn', ['indie', 'rock', 'alt'], 'Privé Live Club FB events-tab', 'https://www.facebook.com/clubprive/events', fb('1772952327294205'),
    a='uksed 19.00; Muster 20.00 (pop rock), Beid 21.00 (rap rock), Around The Sun 22.00 (indie rock), Blix 23.20 (pop); 17+', pu='https://fienta.com/213746', hind={'praegu': '5 €', 'mark': 'early bird', 'allikas': 'FB event, kontrollitud 20.11.2026'}, nb='Kaks allikat: FB event + Fienta (q=rock otsing).'),
 ev('2026-11-27', 'Säde Semper «Peomaagi maania» esitlus + Ulmenthal', ['Säde Semper', 'Ulmenthal'], 'Von Krahl', 'Tallinn', ['punk', 'alt'], 'Rada7.ee FB events-tab', 'https://www.facebook.com/rada7.ee/events', fb('992999307206729'),
    a='algus 19.00; albumiesitlus', nb='Kaks allikat: FB event (Von Krahl, Rada7.ee jt) + Rada7 FB events-tab. Žanr Säde Semperi varasema reliisikirje järgi (pop punk / folk punk); Ulmenthal on East x West Recordsi artist.'),
 ev('2026-12-11', 'Verivorsti Live: Metsatöll @ Hiiu Õlletuba', ['Metsatöll'], 'Hiiu Õlletuba', 'Tallinn', ['folk', 'metal'], 'Rada7.ee FB events-tab', 'https://www.facebook.com/rada7.ee/events', fb('1777276683692380'),
    a='algus 22.00', pu='https://www.piletilevi.ee/piletid/XSZGMQDGL5/metsatoll-verivorsti-live-hiiu-olletoas', nb='Kaks allikat: FB event (Hiiu Õlletuba + Metsatöll) + Piletilevi.'),
 ev('2026-11-27', ':Denzel x The Heinous LIVE @ Kidrakuur', [':Denzel', 'The Heinous'], 'Kidrakuur Kultuuriklubi', 'Tallinn', ['rock'], 'Kidrakuur FB events-tab', 'https://www.facebook.com/KidrakuurKultuuriklubi/events', fb('1114362194803819'),
    a='uksed 20.00; rokk', hind={'praegu': 'tasuta', 'allikas': 'FB event, kontrollitud 20.11.2026'}, nb='Kaks allikat: FB event (:Denzel + Kidrakuur) + Kidrakuuri FB events-tab.'),
 {'d': '2027-07-16', 'd2': '17.07', 't': 'festival', 'n': "Käbliku Beer Camp & Rock'N'Roll 2027", 'b': [], 'koosseis_tba': 1, 'v': 'Käbliku Pruulikoda', 'c': 'mujal', 'g': ['rock'], 'sn': 'Ticketer', 'su': 'https://www.ticketer.ee/', 'on_': 'fest.kabliku.com', 'ou': 'https://fest.kabliku.com/', 'pu': 'https://www.ticketer.ee/kabliku-beer-camp-rocknroll/', 'a': 'Põlvamaa; esinejad veel välja kuulutamata', 'lisatud': T, 'nb': NB + 'Kaks allikat: festivali koduleht (16.–17. juuli 2027, „Esinejad on veel välja kuulutamata“) + Ticketeri avaleht (16–17 juuli, Käbliku turismitalu, Põlva).'},
 rel('2026-11-18', 'B.T. — «Bullshit Live Tape»', ['B.T.'], ['punk'], 'https://balltmusic.bandcamp.com/album/bullshit-live-tape', 'live-lint; egg punk, Tallinn', 'Kuupäev Bandcampi albumilehelt (released November 18, 2026).'),
 rel('2026-11-13', 'Üks kõigi ja kõik ühe eest — «Õigel pool Mahtra sõda»', ['Üks kõigi ja kõik ühe eest'], ['punk'], 'https://yksk6ik.bandcamp.com/album/igel-pool-mahtra-s-da', 'hardcore punk', 'Kuupäev Bandcampi albumilehelt (released November 13, 2026).'),
 rel('2026-11-13', 'VKS — «Kas sitt või moos?»', ['VKS'], ['punk'], 'https://vaatakuissuren.bandcamp.com/album/kas-sitt-v-i-moos', 'punk / hardcore punk / noise rock, Tallinn', 'Kuupäev Bandcampi albumilehelt (released November 13, 2026).'),
 rel('2026-11-01', 'Tallinnfilm — «A3a3a3a!»', ['Tallinnfilm'], ['rock', 'indie', 'alt'], 'https://tallinnfilm.bandcamp.com/album/a3a3a3a', 'indie rock / blues / dream pop, Tallinn', 'Kuupäev Bandcampi albumilehelt (released November 1, 2026).'),
]
new_rap = [
 ev('2026-11-21', 'Chainz Live: Maakuu «Kummuli» & Chainz «Laboratoorium» topelt-albumiesitlus', ['Chainz', 'Maakuu'], 'Legendaarne Raadio & Baar', 'Tallinn', ['hiphop'], 'Legendaarne Raadio FB events-tab', 'https://www.facebook.com/LegendaarneRaadio/events', fb('1467024438726996'),
    a='20.00–03.00', pu='https://fienta.com/et/chainz-live-maakuu-kummuli-chainz-laboratoorium-topelt-albumiesitus', nb='Kaks allikat: FB event + Fienta (q=räpp).'),
 ev('2026-12-18', 'Hip Hop Hangout @ Kultuuriklubi Tempel', ['5LOOPS', 'Loodikud', 'Majaka Mandela', 'Carlotta', 'DJ Kayot', 'Don Nuki', 'Sänk', 'sPOOM', 'Loodikud Krew'], 'Kultuuriklubi Tempel', 'Pärnu', ['hiphop'], 'Loodikud FB events-tab', 'https://www.facebook.com/profile.php?id=61565948540767&sk=events', fb('3132941123719775'),
    a='algus 20.00; räpi-live’id + DJ-d', hind={'praegu': '5 €', 'mark': 'toetus', 'allikas': 'FB event, kontrollitud 20.11.2026'}, nb='Kaks allikat: FB event (Loodikud, Carlotta, Tempel) + Rada7 FB events-tab.'),
 ev('2026-11-27', 'T-Parm «13 Sarvikut» EP esitlus', ['T-Parm', 'Benakanister'], 'Konk', 'Tartu', ['hiphop'], 'Konk FB events-tab', 'https://www.facebook.com/profile.php?id=61593812049749&sk=events', fb('1488082179920217'),
    a='21.00–02.00; debüüt-EP esitlus, lisaks kolm üllatusartisti', hind={'praegu': 'tasuta', 'allikas': 'FB event, kontrollitud 20.11.2026'}, nb='Kaks allikat: FB event (Konk + Aparaaditehas) + Konki FB events-tab.'),
 ev('2026-12-04', 'FOMO: Real Hip-Hop Is Back', ['Shaggy (LV)', 'Bassofsky', 'Da Crew'], 'Paavli Kultuurivabrik', 'Tallinn', ['hiphop'], 'Rada7.ee FB events-tab', 'https://www.facebook.com/rada7.ee/events', fb('1877428257035480'),
    a='algus 23.00; hip-hop / rap / RnB klubiõhtu; 18+', pu='https://gateme.com/Paavlikultuurivabrik-stellar/104574-fomo-real-hip-hop-is-back', nb='Kaks allikat: FB event (FOMO + Paavli) + GateMe piletileht.'),
 ev('2026-12-06', 'EiK | elav muusika & luulekogu esitlus', ['EiK'], 'Von Krahl', 'Tallinn', ['räpp'], 'Rada7.ee FB events-tab', 'https://www.facebook.com/rada7.ee/events', fb('4539907379620619'),
    a='20.00–22.00; bändiga, luulekogu „mis edasi, see alles selgineb“ esitlus', pu='https://piletikeskus.ee/et/e/iff52a', nb='Kaks allikat: FB event + Piletikeskus; Bandsintown liigitab hip-hopiks; EiK on räpisaidil ka varem (EiK LIVE 26.09).'),
]
new_klubi = [
 ev('2026-11-21', 'DnB Special Guest Night @ Kära Kants', ['IDAONTHEDECKZ', 'Dr. Doctor'], 'Kära Kants', 'Rakvere', ['dnb'], 'Kära Kantsi FB grupi events-tab', 'https://www.facebook.com/groups/112392415448166/events', fb('1118637500893323'),
    a='23.00–04.00; 18+', hind={'praegu': 'enne 23 tasuta, pärast 5 €', 'allikas': 'FB event, kontrollitud 20.11.2026'}, nb='Kaks allikat: FB event + Kära Kantsi grupi events-tab.'),
 ev('2026-11-27', 'Compress Rave x HALL: Acid Techno Night', ['Meelis Vili b2b L21 (GE)', 'Charch (GE)', 'QSLAP', 'Bertanxcan (TR)', 'Powerpuff'], 'HALL', 'Tallinn', ['techno'], 'HALL FB events-tab', 'https://www.facebook.com/halltallinn/events', fb('1054018380984487'),
    a='algus 23.00; acid techno; 18+', pu='https://gateme.com/et/halltallinn/104571-compress-rave-x-hall-acid-techno-night', nb='Kaks allikat: FB event (CompressEvents + HALL) + GateMe.'),
 ev('2026-11-28', 'Bar IDA — Saaremets plays house all night long', ['Raul Saaremets'], 'Bar IDA', 'Tallinn', ['house'], 'IDA Radio FB events-tab', 'https://www.facebook.com/IDARadio/events', fb('2568854300262910'),
    a='22.00–04.00', hind={'praegu': '5 €', 'allikas': 'FB event, kontrollitud 20.11.2026'}, nb='Kaks allikat: FB event + IDA Radio FB events-tab.'),
 ev('2026-12-12', 'ÖÖTjuunINg', ['Kalev Rundu', 'JaanJaago', 'Kaspar Leivo', 'L.Eazy', 'To-Sha', 'Qba'], 'Fonoteek', 'Tallinn', ['dnb'], 'Fonoteek FB events-tab', 'https://www.facebook.com/fonoteekbar/events', fb('2348953222522880'),
    a='algus 23.00; Öötöö + Tjuun In, drum & bass', hind={'praegu': '5 € / 10 €', 'mark': 'enne 00.00 5 € (FB going), pärast 10 €', 'allikas': 'FB event, kontrollitud 20.11.2026'}, nb='Kaks allikat: FB event (Tjuun In, Fonoteek, Öötöö) + Fonoteegi FB events-tab.'),
 ev('2026-12-19', 'Selecta: Mozey (UK)', ['Mozey (UK)'], 'D3', 'Tallinn', ['dnb'], 'Resident Advisor', 'https://ra.co/events/2579779', fb('1189954200363190'),
    a='23.00–04.00; jump-up drum & bass', pu='https://gateme.com/D3Tallinn/104427-selecta-mozey-uk-tallinn', nb='Kolm allikat: FB event (Selecta + D3), RA (2579779), GateMe. 13.11 sweepil oli ainult RA — nüüd kinnitatud.'),
 ev('2026-12-19', 'TRIPLOOP invites Kaspiann (FIN)', ['Kaspiann (FIN)', 'Punch', 'Unitøne', 'Brenna Ryan'], 'HALL', 'Tallinn', ['techno'], 'HALL FB events-tab', 'https://www.facebook.com/halltallinn/events', fb('1909012816748721'),
    a='algus 23.00; hüpnootiline / psühhedeeliline techno', pu='https://gateme.com/halltallinn/104577-triploop-invites-kaspiann-fin', nb='Kaks allikat: FB event (TRIPLOOP + HALL) + GateMe.'),
 ev('2027-02-12', 'Selecta x Helitehas B-Day', [], 'Helitehas', 'Tallinn', ['dnb'], 'Helitehas FB events-tab', 'https://www.facebook.com/helitehas/events', fb('4718787808443770'),
    a='22.00–04.00; Selecta 7 + Helitehas 8 sünnipäev, drum & bass', pu='https://gateme.com/et/helitehas/104539-selecta-x-helitehas-b-day', extra={'koosseis_tba': 1}, nb='Kaks allikat: FB event (Selecta + Helitehas) + GateMe. Koosseis avaldamata.'),
 ev('2026-11-20', 'Kaks Tuba x Meisterjaan', ['Meisterjaan'], 'Kaks Tuba', 'Rapla', ['techno', 'electro'], 'Kaks Tuba FB events-tab', 'https://www.facebook.com/kakstuba/events', fb('1917713109637048'),
    a='23.00–04.00; Meisterjaan DJ-setiga („technot, võib-olla natuke elektrot“)', nb='Kaks allikat: FB event (Kaks Tuba + Meisterjaan) + Kaks Tuba FB events-tab.'),
 rel('2026-11-19', 'Darth Phader & Andaaza — «Saunasaundi»', ['Darth Phader', 'Andaaza'], ['psytrance', 'techno'], 'https://adelicrecords.bandcamp.com/album/saunasaundi', 'Adelic Records (Tallinn); suomisaundi / psytrance / techno', 'Kuupäev Bandcampi albumilehelt (released November 19, 2026).'),
 rel('2026-11-18', 'DJ Puu — «esto edits 01»', ['DJ Puu'], ['house'], 'https://djpuu.bandcamp.com/album/esto-edits-01', 'outsider house / lo-fi beats, Tallinn', 'Kuupäev Bandcampi albumilehelt (released November 18, 2026).'),
]
for e in new_rap: e['t'] = 'kontsert'
for e in new_klubi:
    if e['t'] != 'reliis': e['t'] = 'klubi'
for e in new_www:
    if 'Andres Roots' in e['n']: pass
# enrichment
for e in www:
    if e.get('n', '').startswith('Howls of Winter 2027') and 'Thromos (DE)' not in e['b']:
        e['b'].insert(e['b'].index('Hasswald') if 'Hasswald' in e['b'] else len(e['b']), 'Thromos (DE)')
        e['nb'] = e.get('nb', '') + ' | 20.11.2026 sweep: +Thromos (DE) howlsofwinter.eu koosseisust (10 nime, „more to be unveiled“).'
        print('howls ok')
    if e.get('d') == '2026-11-20' and e.get('n', '').startswith('Mustasch') and 'Above My Head' not in e['b']:
        e['b'].append('Above My Head')
        e['nb'] = e.get('nb', '') + ' | 20.11.2026 sweep: erikülaline Above My Head (MuusikaPlaneet 18.11 uudis „Mustaschi reedese kontserdi erikülaliseks kinnitati kodumaine Above My Head“).'
        print('mustasch ok')
www += new_www; rap += new_rap; klubi += new_klubi
save('data/manual.json', www); save('rap/data/manual.json', rap); save('klubi/data/manual.json', klubi)
print(len(new_www), len(new_rap), len(new_klubi))
