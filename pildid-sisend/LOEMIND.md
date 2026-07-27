# pildid-sisend/ — käsitsi salvestatud pisipildid

Siia paned pildid, mida masin ise kätte ei saa. Peamine juhtum on **Facebooki ürituse
kaanepilt**: FB blokib robotid, nõuab sisselogimist ja lingid aeguvad, seega automaatkorje
sinna ei lähe. Sinu brauseris on pilt aga olemas.

## Kuidas

1. Ava ürituse leht, tee kaanepildil parem klõps → **Salvesta pilt kui…**
2. Salvesta siia kausta. **Failinimi = ürituse nime algus**, nt
   `underground laine.jpg`, `roots session x.png`, `gogol bordello.jpg`.
   Suurtähed, tühikud ja täpitähed on lubatud — skript teeb neist ise slugi.
   Kui nimi sobib mitme kirjega, ütleb skript seda ja jätab faili puutumata.
3. Jooksuta `python scripts/fetch_images.py`.
   Pilt skaleeritakse 216 px laiuseks, salvestatakse `pildid/<slug>.webp`,
   kirjesse tuleb `img`-väli ja **sisendfail kustutatakse** (töö on tehtud).

## Sweepi-tehnika (Claude teeb ise, kui Chrome lubab)

FB ürituse lehel töötab see brauseris (Claude-in-Chrome `javascript_tool`) — pilt tõmmatakse
lehe enda kontekstis, skaleeritakse 216 px-le ja lastakse alla `<a download>` kaudu:

```js
const main=document.querySelector('div[role="main"]')||document;
const kand=[...main.querySelectorAll('img')]
  .filter(i=>i.naturalWidth>=400 && new URL(i.src).pathname.includes('/t39.30808-6/'))
  .sort((a,b)=>b.naturalWidth*b.naturalHeight-a.naturalWidth*a.naturalHeight);
const img=kand[0];                       // /t39.30808-6/ = ürituse foto; t51 = story/UI
const bm=await createImageBitmap(await (await fetch(img.src,{mode:'cors'})).blob());
const W=216,H=Math.round(bm.height*W/bm.width);
const c=new OffscreenCanvas(W,H); c.getContext('2d').drawImage(bm,0,0,W,H);
const out=await c.convertToBlob({type:'image/webp',quality:0.8});
const a=document.createElement('a'); a.href=URL.createObjectURL(out); a.download='ürituse nimi.webp';
document.body.appendChild(a); a.click(); a.remove();
```

Fail maandub `Downloads` kausta → tõsta siia → `python scripts/fetch_images.py`.

**⚠ Chrome blokeerib mitu automaatset allalaadimist ühelt saidilt.** Esimene fail tuleb, ülejäänud
mitte. Selleks peab facebook.com-il olema lubatud „Automaatsed allalaadimised" (aadressiribal
tekib blokeerimise ikoon → Luba; või Seaded → Privaatsus → Saidi seaded → Automaatsed
allalaadimised). Ilma selleta tuleb pildid salvestada käsitsi.

**NB pildi valik:** ära võta lihtsalt lehe suurimat pilti — FB külgribas on stories/reels
(`/t51...`), mis on suuremad kui kaanepilt. Filtreeri `/t39.30808-6/` järgi.

## Piirid

- Liiga lai (kuvasuhe üle 2.0) või alla 300 px pilt jäetakse kõrvale — kirje jääb
  tüübimärgi peale. Pilti ei kärbita kunagi, seega tekstiga plakat ei lõhu.
- Alternatiiv käsitsi salvestamisele: pane kirjesse väli `"img_src": "<aadress>"`.
  Skript proovib seda esimesena; see võib olla nii otsene pildi- kui lehe-aadress
  (nt Piletilevi ürituse leht). Facebooki aadressid on ka seal keelatud.
