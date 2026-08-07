# Sweepi pildisamm — valmis tekst prompti kleepimiseks

Lisa see samm `skene-fb-ig-sweep` taski prompti, kohe pärast sammu, kus uued kirjed on
`data/manual.json`-i lisatud (ja enne `fetch.py` jooksutamist).

---

## SAMM: ürituse bänner Facebookist (uutele kirjetele)

Iga kirje kohta, mille sa selles sweepis manual.json-i LISASID või mille FB-ürituse lehel
sa niikuinii käisid, salvesta ürituse kaanepilt. Tee seda ainult siis, kui kirjel EI OLE
juba `img`-välja.

1. Ava ürituse FB-leht (see, mis läks `ou`-välja).
2. Jooksuta seal `mcp__claude-in-chrome__javascript_tool`-iga see kood, kus `NIMI` on
   kirje nime ALGUS väikeste tähtedega (nt `underground laine`, `roots session x`):

**NB: kaks JS-kutset, mitte üks.** Kui fetch + createImageBitmap + allalaadimine on ühes
kutses, jookseb `javascript_tool` CDP 45 s timeouti (kontrollitud 07.08.2026). Jaga pooleks.

**1. kutse — leia kaas ja tõmba blob `window.__blob`-i:**

```js
await new Promise(r=>setTimeout(r,3000));            // lase lehel laadida
const main=document.querySelector('div[role="main"]')||document;
const kand=[...main.querySelectorAll('img')]
  .filter(i=>i.naturalWidth>=400
          && /\/t39\.(30808|99422)-6\//.test(new URL(i.src).pathname)
          && i.naturalWidth/i.naturalHeight<2.0)
  .sort((a,b)=>b.naturalWidth*b.naturalHeight-a.naturalWidth*a.naturalHeight);
if(!kand.length) 'KAANEPILTI EI LEIDNUD';
else{
  const ac=new AbortController(); setTimeout(()=>ac.abort(),8000);
  window.__blob=await (await fetch(kand[0].src,{mode:'cors',signal:ac.signal})).blob();
  'blob '+window.__blob.size+' ('+kand[0].naturalWidth+'x'+kand[0].naturalHeight+')';
}
```

**2. kutse — tee pisipilt ja lae alla** (`NIMI` = kirje nime ALGUS väikeste tähtedega):

```js
const bm=await createImageBitmap(window.__blob);
const W=216,H=Math.round(bm.height*W/bm.width);
const c=new OffscreenCanvas(W,H); c.getContext('2d').drawImage(bm,0,0,W,H);
const out=await c.convertToBlob({type:'image/webp',quality:0.8});
const a=document.createElement('a'); a.href=URL.createObjectURL(out); a.download='NIMI.webp';
document.body.appendChild(a); a.click(); a.remove();
'OK '+bm.width+'x'+bm.height+' -> '+W+'x'+H+' ('+out.size+' B)';
```

3. Kui kõik lehed on läbi käidud, tõsta failid Downloadsist sisendkausta:

```powershell
$dl="$env:USERPROFILE\Downloads"; $siht="C:\Users\Silver\Documents\skene-info\pildid-sisend"
Get-ChildItem $dl -Filter "*.webp" | Where-Object {$_.LastWriteTime -gt (Get-Date).AddHours(-2)} |
  ForEach-Object { Move-Item $_.FullName (Join-Path $siht $_.Name) -Force; $_.Name }
```

4. Jooksuta pildikorje ENNE fetch.py-d (see korjab ka Bandcampi/Piletilevi pildid):

```
python scripts/fetch_images.py
```

5. Alles siis tavaline `fetch.py` / `fetch_klubi.py` / `fetch_rap.py` + `build_api.py`.

### Reeglid, mida mitte unustada
- **Ära võta lehe suurimat pilti.** FB külgribas on stories/reels (`/t51...`), mis on
  kaanepildist suuremad. Filter `/t39.(30808|99422)-6/` on kohustuslik.
- ⚠ **Kaks CDN-teed, mitte üks** (avastatud 07.08.2026): FB serveerib event-kaasi nii
  `/t39.30808-6/` kui `/t39.99422-6/` alt. CHECK ONE TWO lehel oli kaas 960×540
  `99422` all ja `30808` all oli hoopis 350×350 profiilipilt — ainult vana filtriga
  oleks tulnud vale vastus "KAANEPILTI EI LEIDNUD".
- **Canvas'ilt otse joonistada ei saa** — `drawImage(img,…)` teeb canvas'i tainted'iks ja
  `convertToBlob` viskab "Tainted OffscreenCanvas may not be exported". Peab käima
  `fetch` + `createImageBitmap` kaudu, nagu ülal.
- ⚠ **`fetch_images.py` kestab üle 55 s ja Desktop Commanderi shell tapab selle** (ka
  `Start-Process -Wait` puhul). Tulemus: sisendfailid tarbitakse ära, aga `manual.json`-i
  `img`-väljad jäävad kirjutamata — st pildid on kettal, kirjed aga pildita. Jooksuta
  LAHTIÜHENDATUNA (`Start-Process … -WindowStyle Hidden` ilma `-Wait`-ita) ja küsi seisu
  eraldi kutsega; salvestus toimub iga saidi lõpus.
- Kui kood ütleb `KAANEPILTI EI LEIDNUD`, jäta kirje pildita — leht joonistab tüübimärgi.
- Chrome peab lubama facebook.com-ile automaatsed allalaadimised (lubatud 27.07.2026).
  Kui allalaadimisi ei tule, kontrolli aadressiribalt blokeerimise ikooni.
- Failinimi peab olema kirje nime ALGUS. Kui see sobib mitme kirjega, ütleb
  `fetch_images.py` seda ja jätab faili puutumata — täpsusta siis nime.
- Pilti ei kärbita kunagi. Üle 2.0 kuvasuhtega (nt 1200×499) pilt jäetakse kõrvale.
