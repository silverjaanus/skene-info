// Regressioonitest: MITMEPAEVASED KIRJED (bug leitud 15.08.2026).
//
// Mis juhtus: kogu lehe kood otsustas "kas kirje on labi" ainult ALGUSKUUPAEVA jargi
// (e.d < TODAY). 14.-16.08 festival kadus seetottu nimekirjast, kalendrist ja
// kuuloendist juba 15. augustil. 15.08.2026 seisuga oli nii peidus 6 kaimasolevat kirjet.
//
// See test loeb funktsioonid VALJA GENEREERITUD index.html-ist (mitte template'ist),
// ehk kontrollib tapselt seda koodi, mis kasutajani jouab. Kuupaev on fikseeritud,
// nii et test annab sama tulemuse iga paev.
//
//   node scripts/test_kuupaevad.js
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const TODAY = "2026-08-15";           // fikseeritud "tana" - test ei tohi kalendrist soltuda

// --- funktsioonide valjalougimine index.html-ist -------------------------------
function grab(src, name) {
  const i = src.indexOf("function " + name + "(");
  if (i < 0) throw new Error("index.html-ist ei leia funktsiooni: " + name);
  let depth = 0, k = src.indexOf("{", i);
  for (; k < src.length; k++) {
    if (src[k] === "{") depth++;
    else if (src[k] === "}") { depth--; if (depth === 0) { k++; break; } }
  }
  return src.slice(i, k);
}

const NIMED = ["pad2", "dOnly", "addDays", "isoOf", "endDate",
               "lastIso", "onLabi", "effIso", "kuuNext", "kuusOn", "covers",
               "saidiJarjek", "saitOf", "interleaveSaidid", "isRel"];

function laeFn(saitFail) {
  const src = fs.readFileSync(path.join(ROOT, saitFail), "utf8");
  const m = src.match(/const SELF="([a-z]+)"/);
  if (!m) throw new Error(saitFail + ": ei leia SELF-i");
  const kood = NIMED.map(n => grab(src, n)).join("\n")
             + "\nreturn {" + NIMED.join(",") + ",SELF};";
  const F = new Function("TODAY", "SELF", "SAIDID", kood)(TODAY, m[1], ["www", "rap", "klubi"]);
  return F;
}

// --- pisike testiraamistik ----------------------------------------------------
let vigu = 0, ok = 0;
function on(tingimus, mida) {
  if (tingimus) { ok++; return; }
  vigu++;
  console.error("KUKKUS: " + mida);
}
function vordne(saadud, oodatud, mida) {
  on(saadud === oodatud, mida + " (sain " + JSON.stringify(saadud)
     + ", ootasin " + JSON.stringify(oodatud) + ")");
}

// --- testid -------------------------------------------------------------------
for (const fail of ["index.html", "rap/index.html", "klubi/index.html"]) {
  const F = laeFn(fail);
  const nimi = fail + ": ";

  // 1. TAPSELT SEE BUG. Kolmepaevane festival 14.-16.08, "tana" on 15.08.
  const fest = { d: "2026-08-14", d2: "16.08", t: "festival", n: "Dark Side of the Moon 2026" };
  on(!F.onLabi(fest), nimi + "kaimasolev festival EI ole labi");
  on(F.covers(fest, TODAY), nimi + "kalender katab kaimasoleva festivali tanase paeva");
  vordne(F.lastIso(fest), "2026-08-16", nimi + "festivali viimane paev");
  vordne(F.effIso(fest), TODAY, nimi + "silt/jarjestus naitab TANAST, mitte alguskuupaeva");

  // 2. Viimane paev on veel nahtav, jargmine paev mitte.
  const eile = { d: "2026-08-13", d2: "14.08" };
  on(F.onLabi(eile), nimi + "eile loppenud festival ON labi");
  const viimane = { d: "2026-08-13", d2: "15.08" };
  on(!F.onLabi(viimane), nimi + "viimasel paeval on kirje veel nahtav");
  vordne(F.effIso(viimane), TODAY, nimi + "viimasel paeval on eff = tana");

  // 3. Uhepaevased kirjed toimivad endiselt.
  on(F.onLabi({ d: "2026-08-14" }), nimi + "eilne uhepaevane kirje on labi");
  on(!F.onLabi({ d: "2026-08-15" }), nimi + "tanane kirje ei ole labi");
  on(!F.onLabi({ d: "2026-09-01" }), nimi + "tulevane kirje ei ole labi");
  vordne(F.effIso({ d: "2026-09-01" }), "2026-09-01", nimi + "tulevase kirje eff = tema oma kuupaev");
  // A8 (15.08.2026): TBA-l on 60 paeva armuaega, mitte igavik. Vana reegel ("TBA kirje ei ole
  // KUNAGI labi") oleks jatnud 2020. aasta kirje nimekirja igavesti rippuma.
  // ⚠ Sama 60 elab kahes kohas: base.html onLabi (literaal) ja common.py TBA_ARMUAEG.
  on(!F.onLabi({ d: "2026-08-01", tba: true }), nimi + "TBA kirje armuaja sees ei ole labi");
  on(!F.onLabi({ d: "2026-06-17", tba: true }), nimi + "TBA kirje tapselt 60 p vanune ei ole veel labi");
  on(F.onLabi({ d: "2026-06-15", tba: true }), nimi + "TBA kirje ule 60 p vana ON labi");
  on(F.onLabi({ d: "2020-01-01", tba: true }), nimi + "ammune TBA kirje ON labi");
  on(!F.onLabi({ d: "2027-06-17", tba: true }), nimi + "tulevane TBA kirje ei ole labi");

  // 4. Kuufilter: kuudevaheline festival peab olema leitav MOLEMAST kuust.
  const ule = { d: "2026-07-29", d2: "01.08" };
  on(F.kuusOn(ule, "2026-07"), nimi + "juuli-augusti festival kuulub juulisse");
  on(F.kuusOn(ule, "2026-08"), nimi + "juuli-augusti festival kuulub ka augustisse");
  on(!F.kuusOn(ule, "2026-09"), nimi + "... aga mitte septembrisse");
  vordne(F.kuuNext("2026-12"), "2027-01", nimi + "kuuNext ule aastavahetuse");

  // 5. dd-massiiv (tuur aukudega): loeb viimane kuupaev, eff = jargmine tulevane.
  const tuur = { d: "2026-08-10", d2: "20.08", dd: ["2026-08-10", "2026-08-18", "2026-08-20"] };
  on(!F.onLabi(tuur), nimi + "poolelijaanud tuur ei ole labi");
  vordne(F.effIso(tuur), "2026-08-18", nimi + "tuuri eff = jargmine toimumispaev");
  on(!F.covers(tuur, TODAY), nimi + "tuur EI kata paeva, mil esinemist pole");
  on(F.covers(tuur, "2026-08-18"), nimi + "tuur katab oma esinemispaeva");

  // 6. Aastavahetus: d2 = jargmise aasta kuupaev.
  const uusaasta = { d: "2026-12-31", d2: "01.01" };
  vordne(F.lastIso(uusaasta), "2027-01-01", nimi + "aastavahetuse festivali lopp");

  // 7. Paris andmed: uhtki kirjet, mille vahemik katab tanase, ei tohi olla "labi".
  //    (Invariant, mitte konkreetne uritus - test ei vanane koos andmetega.)
  const feed = JSON.parse(fs.readFileSync(path.join(ROOT, "feed", "events.json"), "utf8"));
  let katvad = 0;
  for (const e of (feed.entries || [])) {
    if (!e.d || e.tba) continue;
    if (!F.covers(e, TODAY)) continue;
    katvad++;
    on(!F.onLabi(e), nimi + "paris kirje ei tohi kaduda: " + e.d + " " + e.n);
  }
  on(katvad > 0, nimi + "feedis leidus vahemalt uks tanast katev kirje (kontroll ei jooksnud tuhjalt)");

  // 8. ROUND-ROBIN SAITIDE VAHEL (Silveri otsus 15.08.2026): sama paeva sees
  //    vaheldumisi, alustades OMA saidist. Enne oli plokk (kogu oma sait, siis voorad).
  vordne(F.saidiJarjek()[0], F.SELF, nimi + "round-robin alustab oma saidist");
  vordne(F.saidiJarjek().length, 3, nimi + "jarjekorras on koik kolm saiti");
  vordne(F.saitOf({ d: "2026-09-01" }), F.SELF,
         nimi + "sait-valjata kirje loetakse oma saidi omaks");

  const p = "2026-09-01";
  const rida = (sait, n) => ({ d: p, n: n, sait: sait });
  // Jarjekord on CAT_ORDER-i ROTATSIOON, mitte "oma + ulejaanud tahestikus":
  // www-l www->rap->klubi, rap-il rap->klubi->www, klubi-l klubi->www->rap.
  // Nii sailib uudiskirjaga (common.py CAT_ORDER) sama tsukliline kord.
  const teised = F.saidiJarjek().slice(1);
  // sisend on juba kuupaeva jargi sorditud, uhel paeval 3 oma + 2 voorast
  const sisend = [rida(F.SELF, "oma1"), rida(F.SELF, "oma2"), rida(F.SELF, "oma3"),
                  rida(teised[0], "A1"), rida(teised[0], "A2"), rida(teised[1], "B1")];
  const valjund = F.interleaveSaidid(sisend);
  vordne(valjund.length, sisend.length, nimi + "interleave ei kaota ega paljunda kirjeid");
  vordne(valjund[0].n, "oma1", nimi + "paeva alustab oma sait");
  vordne(valjund[0].sait + "|" + valjund[1].sait + "|" + valjund[2].sait,
         F.SELF + "|" + teised[0] + "|" + teised[1],
         nimi + "esimesed kolm kirjet on kolmelt eri saidilt");
  on(!(valjund[0].sait === valjund[1].sait && valjund[1].sait === valjund[2].sait),
     nimi + "sama saidi kirjed ei ole enam plokis");
  // sama saidi sisemine jarjekord peab sailima
  const omad = valjund.filter(e => e.sait === F.SELF).map(e => e.n).join(",");
  vordne(omad, "oma1,oma2,oma3", nimi + "saidi sisemine jarjekord sailib");

  // eri paevad ei tohi omavahel seguneda
  const kahepaeva = [rida(F.SELF, "x"), { d: "2026-09-02", n: "y", sait: teised[0] }];
  const kp = F.interleaveSaidid(kahepaeva);
  vordne(kp.map(e => e.d).join(" "), "2026-09-01 2026-09-02",
         nimi + "interleave ei sega eri paevi omavahel");

  // uhe saidi paev jaab muutumatuks
  const yks = [rida(F.SELF, "a"), rida(F.SELF, "b")];
  vordne(F.interleaveSaidid(yks).map(e => e.n).join(","), "a,b",
         nimi + "uhe saidi paev jaab samaks");
  vordne(F.interleaveSaidid([]).length, 0, nimi + "tuhi sisend ei kuku");

  // 9. KALENDRIPAEV = URITUS, MITTE RELIIS (Silveri otsus 15.08.2026).
  //    isRel peab kokku langema Pythoni common.is_release()-iga: rel-lipp VOI tuup.
  on(F.isRel({ rel: 1, t: "reliis" }), nimi + "reliis on reliis");
  on(F.isRel({ t: "merch" }), nimi + "merch on reliis/merch");
  on(F.isRel({ rel: 1, t: "kontsert" }), nimi + "rel-lipp loeb ka siis, kui tuup on muu");
  on(!F.isRel({ t: "kontsert" }), nimi + "kontsert ei ole reliis");
  on(!F.isRel({ t: "festival" }), nimi + "festival ei ole reliis");
  on(!F.isRel({ t: "klubi" }), nimi + "klubiohtu ei ole reliis");
  on(!F.isRel({}), nimi + "tuhi kirje ei ole reliis");
  // paris andmed: kas reliisi-moiste tabab neid kirjeid, mida ootame
  const d = JSON.parse(fs.readFileSync(path.join(ROOT, "feed", "events.json"), "utf8"));
  const relKirjed = (d.entries || []).filter(e => F.isRel(e));
  on(relKirjed.every(e => e.rel || e.t === "reliis" || e.t === "merch"),
     nimi + "isRel ei tabanud uhtki uritust");
}

// --- ARHIIVILEHT: sama juur, ainult kuufilter -----------------------------------
// arhiiv.html-il ei ole "labi"-moistet (koik on labi) ega round-robinit, aga kuufilter
// kasutas sedasama `e.d.startsWith(st.kuu)` reeglit -> kuudevaheline festival oli
// leitav ainult alguskuust.
const ARH = ["pad2", "dOnly", "addDays", "isoOf", "lastIso", "kuuNext", "kuusOn"];
for (const fail of ["arhiiv.html", "rap/arhiiv.html", "klubi/arhiiv.html"]) {
  const src = fs.readFileSync(path.join(ROOT, fail), "utf8");
  const A = new Function(ARH.map(n => grab(src, n)).join("\n")
                         + "\nreturn {" + ARH.join(",") + "};")();
  const nimi = fail + ": ";

  const ule = { d: "2026-07-29", d2: "01.08" };
  vordne(A.lastIso(ule), "2026-08-01", nimi + "kuudevahelise festivali lopp");
  on(A.kuusOn(ule, "2026-07"), nimi + "leitav juulist");
  on(A.kuusOn(ule, "2026-08"), nimi + "leitav ka augustist");
  on(!A.kuusOn(ule, "2026-06"), nimi + "ei ole juunis");
  on(!A.kuusOn(ule, "2026-09"), nimi + "ei ole septembris");

  const yks = { d: "2026-03-14" };
  vordne(A.lastIso(yks), "2026-03-14", nimi + "uhepaevase kirje lopp = tema enda paev");
  on(A.kuusOn(yks, "2026-03"), nimi + "uhepaevane kirje oma kuus");
  on(!A.kuusOn(yks, "2026-04"), nimi + "uhepaevane kirje mitte jargmises kuus");

  const uusaasta = { d: "2026-12-31", d2: "01.01" };
  vordne(A.lastIso(uusaasta), "2027-01-01", nimi + "aastavahetuse kirje lopp");
  on(A.kuusOn(uusaasta, "2026-12"), nimi + "aastavahetuse kirje detsembris");

  const tuur = { d: "2026-05-01", d2: "30.06", dd: ["2026-05-01", "2026-06-30"] };
  on(A.kuusOn(tuur, "2026-05") && A.kuusOn(tuur, "2026-06"),
     nimi + "dd-tuur molemas kuus");
  on(!A.kuusOn(tuur, "2026-07"), nimi + "dd-tuur mitte juulis");
}

console.log((vigu ? "KUKKUS" : "OK") + " - " + ok + " kontrolli labitud, " + vigu + " viga");
process.exit(vigu ? 1 : 0);
