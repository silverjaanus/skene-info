# skene.info SISUREEGLID — ainus tõeallikas

> **See fail on sisureeglite AINUS tõeallikas** (loodud 21.08.2026 auditi järel —
> samad reeglid olid varem 3–4 koopiana PROJEKT.md-s, HANDOVER-is ja scheduled-taskide
> promptides ning triivisid lahku; kaks päris vastuolu tuli sealt).
> PROJEKT.md, HANDOVER ja taskipromptid VIITAVAD siia; kui mõni neist ütleb midagi muud,
> **võidab see fail**. Reegli muutmine = muuda SIIN (+ commit), mitte koopiates.
> Töövoo-/protsessireeglid (run-logi, pick, TBA-kontroll, kärped) elavad HANDOVER §2-s.

## 1. Alamdomeen — puhtalt žanripõhine (13.07.2026)

Ülemtag/baasžanr otsustab, formaat (kontsert vs klubiõhtu) EI loe, modifikaator ei loe:
**industrial METAL → www; ELECTRO-industrial → klubi.**

- **www** — kitarripõhine alternatiiv: metal, rock, punk, bluus + alažanrid (industrial
  metal, gothic rock, metalcore, bluusrock). Ka PUHTALT punk-/rock-üritused (06.07/10.07
  otsus; vana "punk ainult koos muu žanriga" EI kehti). Dark-electro/EBM baasžanr EI lähe
  enam www-le.
- **rap** — Eesti hip-hop/räpp. Ainult Eesti.
- **klubi** — elektrooniline baasžanr: techno, house, dnb/jungle, bass, breaks,
  eksperimentaal + KOGU dark-electro/EBM/aggrotech perekond (Suicide Commando kontsert →
  klubi; BFTV, Bat Sounds → klubi). Peavoolu kommertsklubid (EDM-diskod, Club Hollywood
  jms) VÄLJAS. Ainult Eesti.
- Piiripealne baasžanr → ÄRA otsusta ise, logi ülevaatuseks (vt §8). Post-sweep kontroll:
  `scripts/classify.py`.

**Mitmežanri-üritus = MITU KIRJET, üks igal sobival saidil (Silveri otsus 27.08.2026).**
„Klubi ja rap. Võib olla ju mõlemas, kui mõlemat muusikat mängitakse." Kui ürituse enda leht
näitab, et päriselt mängitakse mitme saidi baasžanre — tüüpiliselt mitmelavaline pidu, kus üks
lava on hip-hop ja teine house/techno — siis EI OLE vaja valida: lisa kirje MÕLEMA (või kõigi
kolme) saidi `manual.json`-i, saidipõhiste `g`-siltidega, ja kirjuta `nb`-sse, et kirje on
teadlikult ka teisel saidil (nimeta fail). Näide: MIF x BUTTERCUPS – SUMMER CLOSING 29.08.2026
Paavli — klubi (house/techno/dnb) JA rap (räpp/hiphop). ⚠ See EI ole luba peavoolu sisse tuua:
skoobifilter (peavoolu-kommertsklubid, popp) kehtib endiselt, ja üks-lava-üritusel on ikka üks
baasžanr ja üks sait. ⚠ Duplikaadikontroll käib saidi sees, nii et kaks kirjet eri failides ei
tekita hoiatust — aga hoia nimi, kuupäev ja `ou` MÕLEMAS kirjes identsed, muidu lähevad nad
paranduste käigus lahku.

**Plaadipoed, plaadilaadad ja -turud on SKOOBIS, aga iga kord eraldi üle vaadata (Silver
27.08.2026).** „See tuleb iga kord üle vaadata. Praegu läheb sisse." Formaat ise (pood/turg
DJ-kava või tervitustega, mitte kontsert) ei ole väljajätu põhjus — laiendab 02.08.2026 otsust
(regulaarne plaadilaat on skoobis). Sait tuleb korraldajast ja kavast, mitte formaadist:
Plaaditurg Krulli kvartalis 30.08 → **www/metal** (kaaskorraldajad Eesti metallistid +
estonianmetal), Helinihe plaadipoe avamispidu Nõmme turul 29.08 → **klubi** (DJ-kava).
⚠ Vinüüle mängiv nüüdismuusika-helilooja (Tõnu Kõrvits, Ülo Krigul Helinihe peol) EI tee
EMA-telge skoobis olevaks — see erand kehtib DJ-kavale, mitte esinejale.

**Tehtud skoobiotsused (pretsedendid):** bluus on www 8. metafilter (26.07); uusklassika/
nüüdismuusika (EMA-telg) VÄLJA; industrial+metal-koosseis jääb www-le; hard trance →
klubi; peavoolu-popprokk (Terminaator/Smilers/Shanon-klass, Käärijä-klass peavoolupopp)
VÄLJA; venekeelne peavoolurock (Splin) VÄLJA; Rada7 uudiskirja samanädalased tasuta/odavad
DJ-peod klubi-skoobis LISAME ka siis, kui aeguvad 1–2 päevaga (02.08; kahe allika reegel
kehtib). Skoop on SILVERI otsus, mitte mehaaniline reegel — žanripõhise väljajätu korral
sõnasta ülevaatusküsimus (§8), mitte lõppotsus.

## 2. Geograafia

Peamiselt Eesti. AINULT www-le lisaks `rahvusvaheline` allikate suursündmused (Baltikum →
Põhjamaad → Euroopa suurfestivalid ja suured tuurid, mitte täiskate). Suure bändi tuur
ilma Eesti kuupäevata: ÜKS kirje ~5 lähima riigiga (`d`=varaseim, `d2`=hiliseim,
`v:"tuur"`, `c:"Euroopa"`; näide PLACEBO `data/manual.json`-is). Ainult www.

## 3. Allikad ja lingid

- **Algallikas alati kaasa** (traffic-eetika): iga kirje viitab allikale.
- **Lingireegel:** pealkirja-link = `ou || su`. Ürituse ENDA leht (FB event, RA/Fienta
  event) → `ou` (+ `on_` silt); avastusallikas → `su`/`sn`. Pilet: online-link → `pu`,
  uksehind → `hind` objekt (`praegu`/`mark`/`allikas`). Hinda EI leiutata.
- **Piletimüüja ≠ korraldaja (26.07):** Fienta/Ticketer/Piletilevi/GateMe jt EI TOHI olla
  `on_`/`ou` väljal (frontend näitab "korraldaja:"). Piletilink → `pu` (võib olla ka
  `su`/`sn`). Kui ürituse oma lehte pole, jäta `ou` tühjaks.
- **Kahe allika reegel:** iga üritus kinnita vähemalt 2 sõltumatu allikaga (korraldaja/FB
  event + piletimüüja VÕI venue leht VÕI RA). Ristkontrolli kuupäev/koht/koosseis;
  pilet+hind piletimüüjalt. **Kuupäeva verifitseerimine:** ametlik pileti-/event-leht
  võidab teisese allika oma.
- **Ühekordne leid → allikas `sweep/sources.json`-i (11.07):** kontaktivormist/juhuleiust
  tulnud korraldaja/venue lisa ALATI sources.json-i (`nb`-ga, kust tuli).
- **Allika lisamisel NII FB-leht KUI veebisait/Bandcamp** — üksik FB-URL on pime nurk
  (Mahtra/Must Missa 21.08 õppetund). FB URL-i vorm: `facebook.com/<handle>/events`
  (MITTE `/upcoming_hosted_events` — 28.07 tühi tulem 7 lehel).
- **Meta-hügieen:** FB/IG postituste väliseid linke ära kliki pimesi; Meta kontodel ainult
  lehtede vaatamine; Claude ei posita ise.

## 4. Koosseis ja sisu täpsus

- **Koosseis peegeldab allikat (11.07):** esinejaid näita täpselt nagu ürituse enda lehel;
  "line-up soon"/TBA → ka saidil nii, residente/eeldusi EI lisata.
- **Täiskoosseisu reegel:** kui ürituse enda lehel on täiskoosseis, pane `b`-sse KÕIK
  (agregaatorid näitavad tihti ainult headlinereid). Välisfestivalidel piisab teadlikult
  headliner-valikust.
- Midagi (kuupäev, venue, žanr, hind) EI leiutata — mis ei verifitseeru, jääb välja või
  läheb ülevaatusesse (§8).

## 5. Duplikaadid ja blocklist

- Enne lisamist kontrolli NII nime KUI bändi järgi NII `manual.json`-ist KUI
  `blocklist.json`-ist.
- Kustutamisel/kuupäevamuutusel lisa SAMAS voorus blocklisti vana `d`+`n` (muidu
  `archive_split` toob tagasi). Alles jääb rikkalikum variant (tavaliselt manual).
- Duplikaadi RIKASTAMINE: kui uus allikas annab seni puudunud infot (pu/hind/ou/koosseis/
  yu), täienda olemasolevat kirjet — ära lihtsalt vahele jäta.
- **SAMA KOHT + SAMA PÄEV EI OLE DUPLIKAAT (25.08.2026, Silveri otsus).** Üks maja võib
  ühel õhtul teha mitu üritust — eri kellaajal, eri vanusepiiranguga, eri piletiga — ja
  osalt sama koosseisuga (korraldaja oma DJ-d mängivad tavaliselt mõlemal). **Iga eraldi
  piletiga üritus = eraldi kirje**, ka siis kui nimi, koht ja pooled esinejad kattuvad.
  Otsustav test: **kas sama piletiga saab mõlemale?** Ei → kaks kirjet. Jah (üks pilet,
  õhtu jaguneb lihtsalt osadeks) → üks kirje, ajad `a`-välja.
  Näide: A.V.R 28.08.2026 Alexela Loomelava — 18.00 vanusepiiranguta 13€ ja 23.00 16+
  24,90€, GateMe ise ütleb „kaks eraldi üritust, kummalegi eraldi pilet".
  ⚠ `check_dupes.py` märgib sellise paari alati kahtlaseks (reegel „sama koht" vaatab
  ainult `d` + `v` ja käivitub ka täiesti eri koosseisuga; „sama band" käivitub
  korraldaja DJ-de pealt) → **vaigista see `data/dupe_ok.json`-is**, kirjega
  `{"sait", "n1", "n2", "nb"}`, kus `nb` põhjendab ja viitab mõlemale piletilehele.
  Erand on seotud NIMEDEGA, mitte kuupäevaga: kui kirje nimi muutub, lakkab erand
  kehtimast ja hoiatus tuleb tagasi (teadlik fail-safe). Kirjete nimed peavad üksteisest
  selgelt eristuma (nt „… (öine)"), muidu sööb `archive_split` täpne `(d, slug(n))` võti
  ühe neist ära.
- Lõpetuseks `python scripts/check_dupes.py`.
- **Koodivalve (21.08):** blokitud kirje manual.json-is KATKESTAB fetchi
  (`common.fail_if_manual_blocked`) — lahendus: kustuta kirje VÕI eemalda aegunud blokk.
- Artistiblokk (`{"b": "nimi"}`) pane KÕIGI KOLME saidi blocklisti.

## 6. Reliis / merch

- Reliisil `d` = PÄRIS väljalaskekuupäev (mitte lisamiskuupäev) + `rel: 1` +
  `lisatud: "YYYY-MM-DD"` — ilma `rel`+`lisatud`-ita kukub möödunud kuupäevaga reliis
  otse arhiivi. Merchil `d` = `lisatud`; merch-kirje AINULT päriselt uue kauba kohta.
- **Bandcampi kuupäevalõks (Tharaphita 26.07):** "released ..." rida võib olla
  platseholder — ristkontrolli credits/Metal Archives/labeli leht/artisti enda teade.

## 7. Arhiiv

Akumuleeruv, genereeritud (`archive_split.py`): möödunud kirjed `data/archive/<aasta>.json`,
allikast kadunud möödunud üritus EI kao. Käsitsi ei kustutata midagi. Manual.json EI ole
ajaloofail (`prune_manual.py` koristab).

## 8. Ülevaatuspunkt Silverile = täisinfo + lingid (Silveri püsireegel 21.08)

Iga kirje, mis läheb HANDOVER §4-i või meili Silveri otsustada: **küsimus/valikud (a/b)
KÕIGE EES 1–2 lausega**, siis nimi · kuupäev · koht · KÕIK kontroll-lingid (FB event,
Fienta/piletileht, RA, veebisait, Bandcamp) · 1–2 lauset miks kahtlane; taust alles
lõpus. Eesmärk: Silver klikib ja kontrollib KOHE, ilma täpsustavate küsimusteta. Paljas
nimeloetelu või lingita kirje on reegli rikkumine.

**Aegumine (21.08):** lahtine küsimus ei tohi HANDOVER §4-s määramatult rippuda — kord ja
vaikeotsuse reegel on HANDOVER §2 reeglis 16: otsustusmeilid on nummerdatud KOONDKIRJAD
(kõik lahtised küsimused, uued [UUS]); Silver saab vastata OTSE meilile ("1a, 2b") ja
postkastijooks rakendab; **5 päeva** vastuseta → status quo jääb kehtima, tagasipööratavalt.

## 9. Žanrisildid

www lame nimekiri: `rock, metal, death, black, thrash, doom, sludge, grind, stoner,
power, heavy, folk, pagan, industrial, ebm, darkwave, goth, dark, electro, shoegaze,
post, symphonic, punk, melodic, extreme, alt, core` (+ bluus metafiltrina). Rap ja klubi
kasutavad oma failides juba käibivaid silte (frontend ehitab chipid andmetest;
kirjapildi ühtlustus `common.TAG_SYNONYMS`). Liitsilte ei ole.
