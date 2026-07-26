# templates/ — kolme saidi index.html genereerimine

`index.html`, `rap/index.html` ja `klubi/index.html` olid 85–97% identsed ja parandused
hakkasid driftima (rap/klubi jäid ilma CSS-muutujast, tüübist `muu`, ikoonidest...).
Nüüd tuleb kõik kolm ÜHEST allikast.

## Reegel

**Muuda template'i, mitte `index.html`-i.** Pärast muudatust jooksuta:

    python scripts/build_pages.py

`index.html` failid on nüüd genereeritud väljund. Käsitsi tehtud muudatus neis
kaob järgmisel genereerimisel.

## Kuidas see koosneb

| Fail | Mis seal on |
|---|---|
| `base.html` | Ühine osa (~39 KB). Erinevuskohtades on pesad `{{S001}}` … `{{S077}}` |
| `site-www.json`, `site-rap.json`, `site-klubi.json` | Iga pesa väärtus sellel saidil. Lühike väärtus on kohe kohal; pikk viitab failile: `{"f": "snippets/www/S007.html"}` |
| `snippets/<sait>/Snnn.html` | Pikad pesaväärtused (CSS-plokid, i18n, E_FALLBACK jne) |
| `SLOTS.md` | Kaart: mis igas pesas on, kõigi kolme saidi lõikes |

Otsi õige pesa üles `SLOTS.md`-st (või `grep`-i `base.html`-ist kohta, kus muudatus
peab olema) ja muuda seda.

- **Muudatus, mis peab minema KÕIGILE kolmele saidile** → `base.html`.
- **Ainult ühele saidile** → selle saidi JSON või snippet.

## Kontroll

    python scripts/build_pages.py --check

Ütleb iga faili kohta OK või ERINEB (+ esimese erinevuse rea ja veeru). ERINEB
tähendab, et keegi on `index.html`-i käsitsi muutnud — **kanna see muudatus enne
ülegenereerimist template'i**, muidu see kaob. Väljumiskood on siis 1, nii et
`--check` sobib ka automaatikasse.

## Kust see tuli

Genereeritud 26.07.2026 auditi järel olemasolevatest failidest difflib'iga: pesad
on täpselt need kohad, kus kolm faili tegelikult erinesid. Esimene genereering andis
kõigi kolme originaaliga baithaaval identse tulemuse (nõue, mille all süsteemi sisse
poleks jäetud).

`arhiiv.html` / `allikad.html` on veel eraldi failid — sama mustri võib neile
hiljem laiendada.
