// test_kalender.js -- api/kalender.js puhaste funktsioonide testid (B5b, 16.08.2026).
//
// Endpoint ise teeb vorguparingu, aga FILTREERIMINE ja ICS-i genereerimine on puhtad
// funktsioonid ja neid saab testida ilma serverita. Testime just neid kohti, kus vaikselt
// vale minna saab: mitmepaevased kirjed, aastavahetus, DTEND-i valispiir, 75-oktetine
// reapiir ja CRLF -- kalendrikliendid on nende suhtes karmid ja viga ei ole ekraanil naha,
// vaid ilmneb alles kellegi telefonis.
//
// Kasutus: node scripts/test_kalender.js
"use strict";
const path = require("path");
const K = require(path.join(__dirname, "..", "api", "kalender.js"));

let vigu = 0, ok = 0;
function on(t, mida) { if (t) { ok++; return; } vigu++; console.error("KUKKUS: " + mida); }
function vordne(saadud, oodatud, mida) {
  on(saadud === oodatud, mida + " (sain " + JSON.stringify(saadud) + ", ootasin " + JSON.stringify(oodatud) + ")");
}

const TANA = "2026-08-16";

// --- 1. loppPaev ----------------------------------------------------------------
vordne(K.loppPaev({ d: "2026-08-16" }), "2026-08-16", "uhepaevane");
vordne(K.loppPaev({ d: "2026-08-14", d2: "16.08" }), "2026-08-16", "mitmepaevane");
vordne(K.loppPaev({ d: "2026-12-30", d2: "02.01" }), "2027-01-02", "ule aastavahetuse");
vordne(K.loppPaev({ d: "2026-08-10", d2: "20.08", dd: ["2026-08-10", "2026-08-18"] }),
       "2026-08-18", "dd-massiiv voidab d2 ule");

// --- 2. filtreeri ---------------------------------------------------------------
const A = [
  { d: "2026-08-20", n: "Punk Tartus", t: "kontsert", c: "Tartu", g: ["punk"], sait: "www" },
  { d: "2026-08-20", n: "Metal Tallinnas", t: "kontsert", c: "Tallinn", g: ["metal"], sait: "www" },
  { d: "2026-08-20", n: "Techno", t: "klubi", c: "Tallinn", g: ["techno"], sait: "klubi" },
  { d: "2026-08-14", d2: "17.08", n: "Kaimasolev festival", t: "festival", c: "Tartu", g: ["punk"], sait: "www" },
  { d: "2026-08-10", n: "Eilne", t: "kontsert", c: "Tartu", g: ["punk"], sait: "www" },
  { d: "2026-09-01", n: "TBA kirje", t: "kontsert", c: "Tartu", g: ["punk"], sait: "www", tba: 1 },
];
const nimed = p => K.filtreeri(A, p, TANA).map(e => e.n);

vordne(nimed({}).join("|"), "Punk Tartus|Metal Tallinnas|Techno|Kaimasolev festival",
       "ilma filtrita: moodunud ja TBA jaavad valja, kaimasolev jaab SISSE");
vordne(nimed({ g: "punk" }).join("|"), "Punk Tartus|Kaimasolev festival", "zanrifilter");
vordne(nimed({ c: "Tartu" }).join("|"), "Punk Tartus|Kaimasolev festival", "linnafilter");
vordne(nimed({ t: "festival" }).join("|"), "Kaimasolev festival", "tuubifilter");
vordne(nimed({ s: "klubi" }).join("|"), "Techno", "saidifilter");
vordne(nimed({ s: "www,klubi" }).length, 4, "kaks saiti");
vordne(nimed({ g: "punk,techno" }).join("|"), "Punk Tartus|Techno|Kaimasolev festival",
       "mitu zanri = VOI (uhisosa), mitte JA");
vordne(nimed({ g: "punk", c: "Tallinn" }).length, 0, "kaks filtrit kitsendavad koos");
// Kirje ilma sait-valjata loetakse www omaks (nii on feedis vanemad kirjed).
vordne(K.filtreeri([{ d: "2026-08-20", n: "X", g: [] }], { s: "www" }, TANA).length, 1,
       "sait-valjata kirje = www");

// --- 3. ICS ---------------------------------------------------------------------
const tekst = K.ics(K.filtreeri(A, { g: "punk" }, TANA), "test");
on(tekst.indexOf("\r\n") !== -1, "ICS kasutab CRLF-i (iCalendari noue)");
on(!/[^\r]\n/.test(tekst), "uhtki paljast LF-i ilma CR-ita ei ole");
vordne((tekst.match(/BEGIN:VEVENT/g) || []).length, 2, "kaks VEVENT-i");
vordne((tekst.match(/END:VEVENT/g) || []).length, 2, "kaks END:VEVENT-i");
on(tekst.indexOf("BEGIN:VCALENDAR") === 0, "algab VCALENDAR-iga");
on(/END:VCALENDAR\r\n$/.test(tekst), "lopeb VCALENDAR-iga");
// DTEND on VALISPIIR: uhepaevane 20.08 -> DTEND 21.08. Ilma selleta kaob uritus
// kalendrist ara voi naidatakse valel paeval.
on(tekst.indexOf("DTSTART;VALUE=DATE:20260820") !== -1, "DTSTART on alguspaev");
on(tekst.indexOf("DTEND;VALUE=DATE:20260821") !== -1, "uhepaevase DTEND = jargmine paev");
on(tekst.indexOf("DTEND;VALUE=DATE:20260818") !== -1, "14.-17.08 festivali DTEND = 18.08");

// --- 4. reapikkus (75 oktetti) --------------------------------------------------
const pikk = { d: "2026-08-20", n: "A".repeat(200), t: "kontsert", c: "Tartu", g: ["punk"], sait: "www" };
const t2 = K.ics([pikk], "test");
const ylepikad = t2.split("\r\n").filter(r => Buffer.from(r, "utf8").length > 75);
vordne(ylepikad.length, 0, "uhtki rida ule 75 okteti");
on(t2.indexOf("\r\n ") !== -1, "murtud rida jatkub tuhikuga");
// Tapitahed ei tohi murdmisel katki minna (multibyte UTF-8).
const t3 = K.ics([{ d: "2026-08-20", n: "Õ".repeat(100), g: [], sait: "www" }], "test");
on(t3.indexOf("�") === -1, "murdmine ei lohu tapitahti");

// --- 5. kalendri nimi -----------------------------------------------------------
on(K.kalendriNimi({}).indexOf("skene.info") === 0, "nimi algab skene.info-ga");
on(K.kalendriNimi({ g: "punk", c: "Tartu" }).indexOf("punk") !== -1, "nimi sisaldab zanrit");
on(K.kalendriNimi({ c: "Tartu" }).indexOf("Tartu") !== -1, "nimi sisaldab linna");

console.log((vigu ? "KUKKUS" : "OK") + " - " + ok + " kontrolli labitud, " + vigu + " viga");
process.exit(vigu ? 1 : 0);
