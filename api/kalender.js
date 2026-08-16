// api/kalender.js — FILTRIPOHINE KALENDRITELLIMUS (webcal). B5b, 16.08.2026.
//
// GET /api/kalender?g=punk,post-punk&c=Tartu&t=kontsert&s=www,klubi
//   -> text/calendar, uks VEVENT iga sobiva kirje kohta.
//
// Mote: kasutaja seab saidil filtri ("punk Tartus"), vajutab "telli kalendrisse" ja tema
// telefoni kalender kusib seda URL-i ise regulaarselt juurde. Uksik .ics oli olemas juba
// varem (lehe calLinks), aga see on UHEKORDNE allalaadimine -- tellimus on elav.
//
// ⚠ MIKS `g` ON TOORSILDID, MITTE METAD. Lehel on zanrifiltrid metad ("metal", "dark"),
// mis tulevad GENRE_META kaardist. See kaart elab JS-is (www ja klubi omad on ERINEVAD) ja
// Pythonis (fetch.py). Kui ma teeksin siia NELJANDA koopia, oleks see neljas koht, mis peab
// syncis pusima -- check_dupes valvab juba kolme. Selle asemel laiendab LEHT valitud metad
// toorsiltideks enne URL-i kokkupanekut ja siin toimub ainult lihtne uhisosa-kontroll.
// Kasu: null duplikaati. Hind: URL on pikem ja vana tellimus jaab vana laienduse peale
// (mis on tegelikult pigem hea -- tellimus ei muutu kasutaja selja taga).
//
// ⚠ TOOTAB AINULT www-l. vercel.json host-route teeb alamdomeenil /(.*) -> /<sait>/$1,
// seega klubi.skene.info/api/kalender on 404. Lehe nupp lingib absoluutselt www-le.

const FEED = "https://www.skene.info/feed/events.json";

// --- puhtad funktsioonid (testitavad, vt scripts/test_kalender.js) ---------------

function nimekiri(v) {
  return String(v || "").split(",").map(s => s.trim()).filter(Boolean);
}

// Kirje viimane paev. Sama reegel mis lehel (lastIso): d2 = "PP.KK", voib ule aasta minna.
function loppPaev(e) {
  if (Array.isArray(e.dd) && e.dd.length) return e.dd.slice().sort()[e.dd.length - 1];
  const d = e.d || "";
  if (!e.d2 || d.length < 10) return d;
  const m = /^(\d{1,2})\.(\d{1,2})$/.exec(e.d2);
  if (!m) return d;
  const aasta = parseInt(d.slice(0, 4), 10);
  const kuu = String(parseInt(m[2], 10)).padStart(2, "0");
  const paev = String(parseInt(m[1], 10)).padStart(2, "0");
  let iso = aasta + "-" + kuu + "-" + paev;
  if (iso < d) iso = (aasta + 1) + "-" + kuu + "-" + paev;   // aastavahetus
  return iso;
}

function filtreeri(entries, p, tana) {
  const g = nimekiri(p.g), s = nimekiri(p.s);
  const t = (p.t || "").trim(), c = (p.c || "").trim();
  return (entries || []).filter(e => {
    if (!e.d) return false;
    if (e.tba) return false;                         // kuupaev kinnitamata -> kalendrisse ei pane
    if (loppPaev(e) < tana) return false;            // moodunud
    if (t && e.t !== t) return false;
    if (c && e.c !== c) return false;
    if (s.length && s.indexOf(e.sait || "www") === -1) return false;
    if (g.length && !(e.g || []).some(x => g.indexOf(x) !== -1)) return false;
    return true;
  });
}

function icsEsc(s) {
  return String(s == null ? "" : s)
    .replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,")
    .replace(/\r?\n/g, " ");
}

function ymd(iso) { return String(iso || "").slice(0, 10).replace(/-/g, ""); }

// DTEND on iCalendari VALIS piir (exclusive) -> lopupaev + 1.
function jargmineYmd(iso) {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10).replace(/-/g, "");
}

// ⚠ iCalendari rida ei tohi olla ule 75 oktetti -- pikk SUMMARY tuleb murda ja jarg
// algab TUHIKUGA. Ilma selleta lykkavad monede klientide parserid kogu kirje korvale.
function murra(rida) {
  const bytes = Buffer.from(rida, "utf8");
  if (bytes.length <= 73) return rida;
  const out = [];
  let osa = Buffer.alloc(0);
  for (const ch of rida) {
    const b = Buffer.from(ch, "utf8");
    if (osa.length + b.length > 73) { out.push(osa.toString("utf8")); osa = Buffer.alloc(0); }
    osa = Buffer.concat([osa, b]);
  }
  if (osa.length) out.push(osa.toString("utf8"));
  return out.join("\r\n ");
}

function ics(entries, pealkiri) {
  const read = [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//skene.info//kalendritellimus//ET",
    "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
    "X-WR-CALNAME:" + icsEsc(pealkiri),
    "X-PUBLISHED-TTL:PT6H", "REFRESH-INTERVAL;VALUE=DURATION:PT6H",
  ];
  entries.forEach(e => {
    const algus = String(e.d).slice(0, 10);
    const lopp = loppPaev(e);
    const koht = (e.v || "") + (e.linn ? ", " + e.linn : (e.c && e.c !== "mujal" ? ", " + e.c : ""));
    // ⚠ UID tuleb urituse nimest -- pikk nimi annab pika UID-i. Esimeses versioonis
    // murdsin ainult SUMMARY/LOCATION/DESCRIPTION ja UID jai 224 oktetti pikaks.
    // Sellepara murtakse nyyd KOIK read korraga allpool, mitte vali kaupa.
    const uid = (String(e.n).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "event")
      + "-" + ymd(algus) + "@skene.info";
    const kirjeldus = [e.a || "", e.ou || e.su || ""].filter(Boolean).join(" — ");
    read.push("BEGIN:VEVENT");
    read.push("UID:" + uid);
    read.push("SUMMARY:" + icsEsc(e.n));
    read.push("DTSTART;VALUE=DATE:" + ymd(algus));
    read.push("DTEND;VALUE=DATE:" + jargmineYmd(lopp));
    if (koht) read.push("LOCATION:" + icsEsc(koht));
    if (kirjeldus) read.push("DESCRIPTION:" + icsEsc(kirjeldus));
    if (e.ou || e.su) read.push("URL:" + (e.ou || e.su));
    read.push("END:VEVENT");
  });
  read.push("END:VCALENDAR");
  // Murdmine kaib KOIGI ridade peal uhes kohas -- nii ei saa uus vali kogemata murdmata
  // jaada (see juhtus UID-ga) ja topeltmurdmist ei teki, sest murra() jookseb korra.
  return read.map(murra).join("\r\n") + "\r\n";   // iCalendar nouab CRLF
}

// Inimloetav kalendri nimi filtri pealt: "skene.info — punk, Tartu".
function kalendriNimi(p) {
  const osad = [];
  const g = nimekiri(p.g), s = nimekiri(p.s);
  if (p.t) osad.push(p.t);
  if (g.length) osad.push(g.slice(0, 4).join("/") + (g.length > 4 ? "…" : ""));
  if (p.c) osad.push(p.c);
  if (s.length && s.length < 3) osad.push(s.join("+"));
  return "skene.info" + (osad.length ? " — " + osad.join(", ") : "");
}

// --- Verceli handler -------------------------------------------------------------

module.exports = async function handler(req, res) {
  if (req.method !== "GET" && req.method !== "HEAD") {
    res.status(405).json({ error: "ainult GET" });
    return;
  }
  try {
    const r = await fetch(FEED, { headers: { "User-Agent": "skene.info kalender" } });
    if (!r.ok) throw new Error("feed " + r.status);
    const j = await r.json();
    const tana = new Date().toISOString().slice(0, 10);
    const valitud = filtreeri(j.entries || [], req.query || {}, tana);
    const tekst = ics(valitud, kalendriNimi(req.query || {}));
    res.setHeader("Content-Type", "text/calendar; charset=utf-8");
    res.setHeader("Content-Disposition", 'inline; filename="skene.ics"');
    // Kalendrikliendid kusivad seda URL-i ise regulaarselt; pool tundi vahekaies on
    // piisav varskus ja hoiab feedi paringud madalal.
    res.setHeader("Cache-Control", "public, max-age=1800, stale-while-revalidate=3600");
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.status(200).send(tekst);
  } catch (err) {
    // Kalendriklient ootab kalendrit ka vea korral -- tyhi, aga KEHTIV kalender on
    // parem kui 500, mis paneks moned kliendid tellimust maha votma.
    res.setHeader("Content-Type", "text/calendar; charset=utf-8");
    res.status(200).send(ics([], "skene.info (ajutine torge)"));
  }
};

module.exports.filtreeri = filtreeri;
module.exports.ics = ics;
module.exports.loppPaev = loppPaev;
module.exports.kalendriNimi = kalendriNimi;
module.exports.murra = murra;
