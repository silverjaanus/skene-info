# templates/ — saidi HTML-lehtede genereerimine

Kolme saidi (www / rap / klubi) lehed olid 79–97% identsed ja parandused hakkasid driftima
(rap/klubi jäid ilma CSS-muutujast, tüübist `muu`, ikoonidest...). Nüüd tuleb iga lehepere
ÜHEST allikast.

Kaetud: **index**, **arhiiv**, **allikad** — kokku 9 genereeritud faili.

## Reegel

**Muuda template'i, mitte genereeritud HTML-i.** Pärast muudatust:

    python scripts/build_pages.py           # kõik
    python scripts/build_pages.py index     # ainult üks lehepere

`index.html`, `arhiiv.html`, `allikad.html` (ja rap/, klubi/ omad) on genereeritud väljund.
Käsitsi tehtud muudatus neis kaob järgmisel genereerimisel.

## Kuidas see koosneb

    templates/<leht>/base.html              ühine osa, erinevuskohtades pesad {{S001}}...
    templates/<leht>/site-<sait>.json       iga pesa väärtus sellel saidil
    templates/<leht>/snippets/<sait>/*.html pikad pesaväärtused (CSS, i18n, E_FALLBACK...)
    templates/<leht>/SLOTS.md               kaart: mis igas pesas on, kõigi 3 saidi lõikes

JSON-is on lühike väärtus kohe kohal; pikk viitab failile: `{"f": "snippets/www/S007.html"}`.

Praegune maht: index 77 pesa (39 KB ühist), arhiiv 24 pesa (20 KB), allikad 10 pesa (5 KB).

- **Muudatus KÕIGILE kolmele saidile** → `<leht>/base.html`.
- **Ainult ühele saidile** → selle saidi JSON või snippet.

Õige koha leiad `SLOTS.md`-st või grep'iga `base.html`-ist ja `snippets/`-ist.

## Kontroll

    python scripts/build_pages.py --check

Iga faili kohta OK või ERINEB (+ esimese erinevuse rida ja veerg), väljumiskood 1 kui erineb.
ERINEB tähendab, et keegi on genereeritud HTML-i käsitsi muutnud — **kanna see muudatus enne
ülegenereerimist template'i**, muidu see kaob.

## Reavahetused

Template hoiab alati LF-i. Väljund kirjutatakse selles konventsioonis, mis sihtfailis juba on.
Nii ei anna `--check` valehäiret teises kloonis ega teisel platvormil (repos on CRLF ja LF
segamini ning `core.autocrlf=true` muudab neid kloonimisel). Sellepärast normaliseerib
generaator sisendi enne võrdlemist — ilma selleta paistsid `allikad.html` failid 0% sarnased,
kuigi olid tegelikult ~79% identsed.

## Kust see tuli

Genereeritud 26.07.2026 auditi järel olemasolevatest failidest difflib'iga: pesad on täpselt
need kohad, kus failid tegelikult erinesid. Esimene genereering andis kõigi üheksa originaaliga
baithaaval identse tulemuse — see oli tingimus, mille all süsteem üldse sisse jäeti.
