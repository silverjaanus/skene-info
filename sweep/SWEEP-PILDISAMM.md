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

```js
await new Promise(r=>setTimeout(r,2000));            // lase lehel laadida
const main=document.querySelector('div[role="main"]')||document;
const kand=[...main.querySelectorAll('img')]
  .filter(i=>i.naturalWidth>=400 && new URL(i.src).pathname.includes('/t39.30808-6/'))
  .sort((a,b)=>b.naturalWidth*b.naturalHeight-a.naturalWidth*a.naturalHeight);
if(!kand.length) 'KAANEPILTI EI LEIDNUD';
else{
  const img=kand[0];
  const bm=await createImageBitmap(await (await fetch(img.src,{mode:'cors'})).blob());
  const W=216,H=Math.round(bm.height*W/bm.width);
  const c=new OffscreenCanvas(W,H); c.getContext('2d').drawImage(bm,0,0,W,H);
  const out=await c.convertToBlob({type:'image/webp',quality:0.8});
  const a=document.createElement('a'); a.href=URL.createObjectURL(out); a.download='NIMI.webp';
  document.body.appendChild(a); a.click(); a.remove();
  'OK '+bm.width+'x'+bm.height+' -> '+W+'x'+H+' ('+out.size+' B)';
}
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
  kaanepildist suuremad. Filter `/t39.30808-6/` on kohustuslik.
- Kui kood ütleb `KAANEPILTI EI LEIDNUD`, jäta kirje pildita — leht joonistab tüübimärgi.
- Chrome peab lubama facebook.com-ile automaatsed allalaadimised (lubatud 27.07.2026).
  Kui allalaadimisi ei tule, kontrolli aadressiribalt blokeerimise ikooni.
- Failinimi peab olema kirje nime ALGUS. Kui see sobib mitme kirjega, ütleb
  `fetch_images.py` seda ja jätab faili puutumata — täpsusta siis nime.
- Pilti ei kärbita kunagi. Üle 2.0 kuvasuhtega (nt 1200×499) pilt jäetakse kõrvale.
