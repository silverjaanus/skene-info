# Sweepi pildisamm — ürituse bänner Facebookist

> **Seis 31.08.2026:** see samm on nüüd **sweepi prompti sees** (`skene-fb-ig-sweep`
> SKILL.md, samm 5b) — see fail on tehniline viide ja õppetundide loend, mitte enam
> „kleepimiseks mõeldud tekst". Silveri otsused 31.08: (a) pildisamm käib sweepiga kaasa,
> (b) faili edastus käib `scripts/pilt_sisendisse.py` kaudu, (c) lai bänner tohib olla riba
> (`MAX_SUHE` 2.0 → **2.8**).

## Miks seda sammu üldse on vaja

`fetch_images.py` korjab `og:image`-i automaatselt (Fienta, GateMe, Piletilevi, Bandcamp,
korraldajate omad saidid — proovib `su` → `ou` → `pu`). **Facebook ja Instagram on
`KEELATUD_HOST`-is**: serveripoolne päring saab sisselogimisseina, mitte pilti. Seega on
FB-eventi kaanepilt AINUS pildiallikas, mille peab võtma brauserikihist.

31.08.2026 seis: 141 tulevast kirjet, 109 pildiga (77%). Pildita 32, neist **15 on
FB-lingiga** — täpselt need, mida see samm katab.

---

## SAMM: bänner FB-eventilt (uutele kirjetele)

Tee seda iga kirje kohta, mille sa selles jooksus `manual.json`-i LISASID ja millel EI OLE
juba `img`-välja. Ürituse FB-leht on niikuinii lahti (sealt tuli `ou`).

**NB: kaks JS-kutset, mitte üks.** Kui fetch + createImageBitmap + allalaadimine on ühes
kutses, jookseb `javascript_tool` CDP 45 s timeouti (kontrollitud 07.08.2026).

### 1. kutse — leia kaas ja tõmba blob `window.__blob`-i

```js
await new Promise(r=>setTimeout(r,3000));            // lase lehel laadida
const main=document.querySelector('div[role="main"]')||document;
const kand=[...main.querySelectorAll('img')]
  .filter(i=>i.naturalWidth>=400
          && /\/t39\.(30808|99422)-6\//.test(new URL(i.src).pathname)
          && i.naturalWidth/i.naturalHeight<2.8)
  .sort((a,b)=>b.naturalWidth*b.naturalHeight-a.naturalWidth*a.naturalHeight);
if(!kand.length) 'KAANEPILTI EI LEIDNUD';
else{
  const ac=new AbortController(); setTimeout(()=>ac.abort(),8000);
  window.__blob=await (await fetch(kand[0].src,{mode:'cors',signal:ac.signal})).blob();
  'blob '+window.__blob.size+' ('+kand[0].naturalWidth+'x'+kand[0].naturalHeight+')';
}
```

### 2. kutse — tee pisipilt ja lae alla

`SLUG` = `common.slug(kirje nimi)` — sama, mida `fetch_images.py` ootab. Kui sa sluggi
peast ei tea, kõlbab ka kirje nime ALGUS väiketähtedega; `pilt_sisendisse.py` sobitab selle.

```js
const bm=await createImageBitmap(window.__blob);
const W=216,H=Math.round(bm.height*W/bm.width);
const c=new OffscreenCanvas(W,H); c.getContext('2d').drawImage(bm,0,0,W,H);
const out=await c.convertToBlob({type:'image/webp',quality:0.8});
const a=document.createElement('a'); a.href=URL.createObjectURL(out); a.download='SLUG.webp';
document.body.appendChild(a); a.click(); a.remove();
'OK '+bm.width+'x'+bm.height+' -> '+W+'x'+H+' ('+out.size+' B)';
```

### 3. Downloadsist sisendkausta — ÜKS KÄSK, kontrolliga

```
python scripts/pilt_sisendisse.py --downloads
```

Skript liigutab viimase 2 h `.webp`/`.jpg`/`.png` failid `pildid-sisend/`-i, **aga ainult
need, mille nimi sobitub mõne `manual.json` kirjega**. Sobimatu fail jääb Downloadsi ja
raporteeritakse reaga `JATAN … ei sobitunud`. Vana ad hoc PowerShelli one-liner tõstis
kõik varsked failid vaikselt üle — kui nimi ei klappinud, jäi kirje pildita ja keegi ei
märganud.

Muud sisendid samas skriptis:

```
python scripts/pilt_sisendisse.py --fail C:\tee\plakat.png --nimi "Kirje nimi"
python scripts/pilt_sisendisse.py --json sweep/_pildid.json     # [{"n":…,"b64":…}]
```

### 4. Pildikorje, siis alles fetch

```
python scripts/fetch_images.py        # tarbib pildid-sisend/ ära, kirjutab img-väljad
python scripts/fetch.py ; python scripts/fetch_rap.py ; python scripts/fetch_klubi.py
```

---

## Reeglid, mida mitte unustada

- ⚠ **Base64 ja URL EI TULE brauserist läbi** (kontrollitud 31.08.2026). Katsed tagastada
  pilt `btoa(...)`-na või anda CDN-i URL Pythonile lõppesid mõlemad filtriga
  `[BLOCKED: Base64 encoded data]` / `[BLOCKED: Cookie/query string data]`. **Brauseri enda
  allalaadimine on ainus toimiv transport** — ära raiska aega nutikamale lahendusele.
- **Ära võta lehe suurimat pilti.** FB külgribas on stories/reels (`/t51...`), mis on
  kaanepildist suuremad. Filter `/t39.(30808|99422)-6/` on kohustuslik.
- ⚠ **Kaks CDN-teed, mitte üks** (07.08.2026): FB serveerib event-kaasi nii `/t39.30808-6/`
  kui `/t39.99422-6/` alt. CHECK ONE TWO lehel oli kaas 960×540 `99422` all ja `30808` all
  hoopis 350×350 profiilipilt.
- **Canvas'ilt otse joonistada ei saa** — `drawImage(img,…)` teeb canvas'i tainted'iks ja
  `convertToBlob` viskab "Tainted OffscreenCanvas may not be exported". Peab käima `fetch`
  + `createImageBitmap` kaudu, nagu ülal.
- ⚠ **`fetch_images.py` kestab kaua** (klubi-pool üksi >7 min, kogu jooks ~15 min) ja
  Desktop Commanderi shell tapab 55 s pealt. Jooksuta lahtiühendatuna
  (`Start-Process … -NoNewWindow` ILMA `-Wait`-ita, logi faili) ja küsi seisu eraldi
  kutsega; salvestus toimub iga saidi lõpus.
- **Kuvasuhte piir on 2.8** (`MAX_SUHE`, Silveri otsus 31.08.2026 „bänner võib ribana
  olla"). Pilti ei kärbita kunagi — lai pilt renderdub madala ribana. Üle 2.8 (nt PLACEBO
  1750×377 = 4.6) jääb ikka välja, sest riba oleks 216×47 px.
- Kui kood ütleb `KAANEPILTI EI LEIDNUD`, jäta kirje pildita — leht joonistab tüübimärgi.
- Chrome peab lubama facebook.com-ile automaatsed allalaadimised (lubatud 27.07.2026).
  Kui allalaadimisi ei tule, ütleb `pilt_sisendisse.py --downloads` seda otse.
