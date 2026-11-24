import re
p = 'HANDOVER.md'
L = open(p, encoding='utf-8').read().split('\n')
move_dates = ['22.10.2026', '23.10.2026', '25.10.2026', '26.10.2026', '01.11.2026', '02.11.2026', '03.11.2026', '04.11.2026', '05.11.2026', '06.11.2026', '07.11.2026', '08.11.2026', '09.11.2026']
moved, keep = [], []
for ln in L:
    m = re.match(r'\*\*Postkastijooks (\d\d\.\d\d\.2026)', ln)
    if m and m.group(1) in move_dates:
        moved.append(ln)
    else:
        keep.append(ln)
# collapse double blank lines
out = []
for ln in keep:
    if ln == '' and out and out[-1] == '':
        continue
    out.append(ln)
NEW = ("**Viimati uuendatud:** 2026-11-20 (nädalane sweep, R 03:05 cron) — **32 uut kirjet: www 17 / rap 5 / klubi 10** (sh 6 reliisi) + 3 rikastust. "
"Katvus: **273 allikat, 222 avatud, 51 skipitud** (35 RA lehte → `ra_snapshot.json` 19.11; 7 Bandcampi kontot → check_bandcamp.py; 2 Spotify; 4 FB otsingu-URL-i; Nailboard arhiveeritud; Tartu Rock Fest 2026 möödunud event; kluub.ee Tallinn = postkastijooks; täisnimekiri `sweep/run-2026-11-20.json`). "
"FB events-tabid sisemise brauseriga (1280×1600, teadaolevad FB id-d base36 `window.name`-is, filter näitab ainult tundmatuid). "
"**Uued www:** DORO 06.06.2027 Helitehas (https://www.facebook.com/events/1080037155063845/) · Andres Roots & Louie Digman 16.12 Salong Tartu (https://www.facebook.com/events/1105196728797899/), 17.12 Konservatoorium Viljandi (https://www.facebook.com/events/1391669420701934/), 18.12 Valga Rockiklubi (https://www.facebook.com/events/1157649303512026/), 19.12 Kidrakuur (https://www.facebook.com/events/1423297816173491/) · Teravmoon jõulupidu 11.12 Kidrakuur (https://www.facebook.com/events/1159653486949117/) · Juudase öö: Mandarones + Kaibald 12.12 Tõrva (https://www.facebook.com/events/1122366903993551/) · Sünge Sünkar 32 19.12 Tempel Pärnu (https://www.facebook.com/events/3041820366155000/) · Tallinn Indie Shuffle 05.12 Privé (https://www.facebook.com/events/1772952327294205/) · Säde Semper + Ulmenthal 27.11 Von Krahl (https://www.facebook.com/events/992999307206729/) · Metsatöll Hiiu Õlletuba 11.12 (https://www.facebook.com/events/1777276683692380/) · :Denzel x The Heinous 27.11 Kidrakuur (https://www.facebook.com/events/1114362194803819/) · Käbliku Beer Camp 2027 16.–17.07 (https://fest.kabliku.com/, koosseis_tba) · reliisid B.T. «Bullshit Live Tape» (https://balltmusic.bandcamp.com/album/bullshit-live-tape), Üks kõigi ja kõik ühe eest «Õigel pool Mahtra sõda» (https://yksk6ik.bandcamp.com/album/igel-pool-mahtra-s-da), VKS «Kas sitt või moos?» (https://vaatakuissuren.bandcamp.com/album/kas-sitt-v-i-moos), Tallinnfilm «A3a3a3a!» (https://tallinnfilm.bandcamp.com/album/a3a3a3a). "
"**Uued rap:** Chainz/Maakuu topelt-esitlus 21.11 Legendaarne (https://www.facebook.com/events/1467024438726996/) · Hip Hop Hangout 18.12 Tempel (https://www.facebook.com/events/3132941123719775/) · T-Parm «13 Sarvikut» 27.11 Konk (https://www.facebook.com/events/1488082179920217/) · FOMO 04.12 Paavli (https://www.facebook.com/events/1877428257035480/) · EiK luulekogu-õhtu 06.12 Von Krahl (https://www.facebook.com/events/4539907379620619/). "
"**Uued klubi:** DnB Special Guest Night 21.11 Kära Kants (https://www.facebook.com/events/1118637500893323/) · Compress Rave 27.11 HALL (https://www.facebook.com/events/1054018380984487/) · Saaremets @ Bar IDA 28.11 (https://www.facebook.com/events/2568854300262910/) · ÖÖTjuunINg 12.12 Fonoteek (https://www.facebook.com/events/2348953222522880/) · Selecta: Mozey 19.12 D3 (https://www.facebook.com/events/1189954200363190/) · TRIPLOOP × Kaspiann 19.12 HALL (https://www.facebook.com/events/1909012816748721/) · Selecta x Helitehas B-Day 12.02.2027 (https://www.facebook.com/events/4718787808443770/) · Kaks Tuba x Meisterjaan 20.11 Rapla (https://www.facebook.com/events/1917713109637048/) · reliisid Darth Phader & Andaaza «Saunasaundi» (https://adelicrecords.bandcamp.com/album/saunasaundi), DJ Puu «esto edits 01» (https://djpuu.bandcamp.com/album/esto-edits-01). "
"**Rikastused:** Howls of Winter 2027 +Thromos (DE) · Mustasch 20.11 +Above My Head (MuusikaPlaneet) · Kurjam LEGE 11.12 +Sollad. 9 FB-kaanepilti (samm 8a), nädalapildil pildita ridu 0 (10 lehte, 47 kirjet + 14 üle ääre). "
"**VÄLJA (žanr/allikas puudub):** Bar IDA: Plastik 27.11 (https://www.facebook.com/events/2601908953591171/) · Machine Nation 18.12 HALL (lineup+žanr TBA, https://www.facebook.com/events/1938695570433585/) · ISOLA X 11.12 HALL (privaatpidu, žanrita, https://www.facebook.com/events/2315382919310567/) · MANIC b2b SULANDI 27.11 huba (https://www.facebook.com/events/1628266008980277/) · /diːp kʌts/ 20.11 huba (https://www.facebook.com/events/2038549646838375/) · Kriminaalne Elevant 27.11 Kinomaja (https://www.facebook.com/events/1877634637004337/) · Subuki 21.11 Viljandi (https://www.facebook.com/events/1807902096793391/) · Meelik ja Alonette 10.12 Paavli (Meeliku žanr lehel puudub, https://www.facebook.com/events/2651053758677437/) · Valter Nõmm allnighter 20.11 Burger Box (https://www.facebook.com/events/2525613084515480/) · Terminal Live: GØK2 & Luka 27.11 (https://www.facebook.com/events/1497648022260429/) · Bass & Häng 11.12 CLWDS (üks allikas, https://www.facebook.com/events/2557299308100307/) · Signaal 20.11 Tempel (žanrita, https://www.facebook.com/events/1785235462744470/) · Pirata Boing 16.12 Kivi (reggae/cumbia, https://www.facebook.com/events/1171697769134209/) · Eino Järvelin 10.12 MOD (iskelmä, https://www.facebook.com/events/1431270025785443/) · 5MIINUST RÖST 16.12 (komöödia, https://www.facebook.com/events/1110094348216115/) · Nikita Grigoriev 26.11 Saar Cult (psühholoogia-loeng, https://www.facebook.com/events/1519427540234951/). "
"**OTSUSTUSPUNKTID [UUS] (sweep/otsused.json):** Rudimental DJ set 19.02.2027, Rivo Haavandi «Oneless», Provincial Beat I 05.12 Viljandi. "
"**classify.py:** 28 konflikti, uutest ainult Last.fm nimekokkulangevused (B.T.→trance BT, T-Parm→UK band, Hip Hop Hangouti Carlotta/sPOOM) — ei liiguta; raport `sweep/classify_report.md`. "
"**⚠ GIT PUSH:** Windowsi Git Credential Manager jäi push'il interaktiivset sisselogimist ootama (fetch töötas) — push tehti `gh auth git-credential` abil (`.swtmp/push.cmd` muster: `git -c credential.helper= -c \"credential.helper=!gh auth git-credential\" push`). Soovitus: Silver uuendab GCM-i GitHubi tokenit. "
"**Allikahooldus:** puhastebeer.com/ollepidu 401, fienta.com/s/kolmnurk 404, kultuurikeskus.ee/underground suunab 2019 lehele, rada7.ee = arhiiv, tolm.trt suletud (tegutses 01–09.2026), tuleb.ee TLS-viga, Psühhoteek FB-leht kadunud. Intro-plokk aegus 06.11 → uudiskirjas pole.")
for i, ln in enumerate(out):
    if ln.startswith('**Viimati uuendatud:**'):
        out[i] = NEW
        break
open(p, 'w', encoding='utf-8').write('\n'.join(out))
a = open('HANDOVER-ARCHIVE.md', encoding='utf-8').read().rstrip('\n')
a += '\n\n## Kärbe 2026-11-20 (sweep) — postkastijooksud 22.10–09.11 verbatim\n\n' + '\n\n'.join(moved) + '\n'
open('HANDOVER-ARCHIVE.md', 'w', encoding='utf-8').write(a)
print('moved', len(moved), 'lines now', len(out))
