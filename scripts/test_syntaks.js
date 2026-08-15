// test_syntaks.js -- kontrollib, et GENEREERITUD lehtede inline-JS on susintaktiliselt korrektne.
//
// MIKS SEE OLEMAS ON (15.08.2026). Lehed pannakse kokku slottidest: base.html + site-<sait>.json
// + snippets/. Iga sait saab OMA kombinatsiooni. See tahendab, et kaks tukki, mis eraldi on
// moistlikud, voivad KOKKU PANDULT olla katkised -- ja ainult uhel saidil kolmest.
//
// Paris juhtum: base.html-i uus rida `const _ft=document.getElementById('ftog')` sattus samasse
// funktsiooni rapi S077-ga, kus oli juba `var _ft`. `const` + `var` sama nimega samas skoobis =
// SyntaxError, mis tappis rap.skene.info-l KOGU lehe skripti. www ja klubi tootasid, sest neil
// on teine S077. Ilma selle kontrollita oleks see laivi lainud.
//
// Kontroll on tahtlikult rumal: parsime, aga EI JOOKSUTA. Seega ei ole vaja DOM-i ega andmeid --
// ainult see, kas brauser suudaks faili uldse ette votta.
//
// Kasutus:
//   node scripts/test_syntaks.js
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");

const LEHED = [
  "index.html", "rap/index.html", "klubi/index.html",
  "arhiiv.html", "rap/arhiiv.html", "klubi/arhiiv.html",
  "allikad.html", "rap/allikad.html", "klubi/allikad.html",
];

// Vota koik <script> plokid, millel POLE src-atribuuti (need on inline-kood).
function inlineSkriptid(src) {
  const out = [];
  const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(src)) !== null) {
    if (/\bsrc\s*=/i.test(m[1])) continue;                 // valine fail
    if (/\btype\s*=\s*["'](?!text\/javascript)/i.test(m[1])) continue;  // nt application/ld+json
    out.push({ kood: m[2], rida: src.slice(0, m.index).split("\n").length });
  }
  return out;
}

let vigu = 0, plokke = 0;
for (const leht of LEHED) {
  const fail = path.join(ROOT, leht);
  if (!fs.existsSync(fail)) { console.error("PUUDUB: " + leht); vigu++; continue; }
  const src = fs.readFileSync(fail, "utf8");
  const plokid = inlineSkriptid(src);
  if (!plokid.length) { console.error("KAHTLANE: " + leht + " -- inline-skripti ei leitud"); vigu++; continue; }
  for (const p of plokid) {
    plokke++;
    try {
      // new Function PARSIB koodi, aga ei jooksuta seda.
      new Function(p.kood);
    } catch (ex) {
      vigu++;
      console.error("SUNTAKSIVIGA: " + leht + " (script algab real ~" + p.rida + ")");
      console.error("   " + ex.name + ": " + ex.message);
    }
  }
}

if (vigu) {
  console.error("KUKKUS - " + plokke + " skriptiplokki, " + vigu + " viga");
  process.exit(1);
}
console.log("OK - " + plokke + " skriptiplokki " + LEHED.length + " lehel, suntaksivigu ei ole");
