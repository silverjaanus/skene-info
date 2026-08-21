// api/agentmail-hook.js -- AgentMaili "unauthenticated" karantiini avaja
//
// POST /api/agentmail-hook   <- AgentMaili webhook, event_type message.received.unauthenticated
//
// PROBLEEM (21.08.2026): kui saatja kirjal PUUDUVAD SPF/DKIM paised, ei viska AgentMail
// kirja ara, vaid annab sildi "unauthenticated". Selle sildiga kiri EI TULE uhessegi
// API-listingusse -- ei list_messages, ei list_threads, ei search, ka mitte
// includeSpam+includeTrash'iga. Ainus viis kirjani jouda on thread_id, mille saab
// ainult konsooli UI-st. Postkastijooks (Claude) ei nae kirja uldse ara.
// Paavli Kultuurivabriku Mailchimpi kirjad (mcsv.net / mcdlv.net) kukuvad sinna
// kord-korralt sisse -- 18.08 ja 21.08 kirjad jaid mitu paeva marakamata.
//
// LAHENDUS: AgentMail POSTib siia sundmuse (ainus koht, kus thread_id valja paistab),
// funktsioon eemaldab threadilt sildi -> kiri ilmub tavalisse listingusse -> olemasolev
// postkastijooks tootab muutmata kujul. Vt docs.agentmail.to/knowledge-base/inbound-emails-missing
//
// MIKS AINULT TUNTUD SAATJAD: "unauthenticated" on paris kaitse -- puuduvad SPF/DKIM
// tahendavad, et saatjat ei saa toestada ja aadressi saab voltsida. Kui silt eemaldada
// koigilt, kaob kaitse tapselt selles postkastis, kuhu Claude ise sisu kaevandab.
// Seetottu on all kitsas domeeninimekiri. UUE uudiskirja tellimisel lisa domeen siia.
//
// Vercel env (Production + Preview):
//   AGENTMAIL_API_KEY      <- AgentMaili API voti (konsool -> API Keys)
//   AGENTMAIL_HOOK_SECRET  <- ise valitud pikk juhuslik sone; SAMA vaartus laheb
//                             AgentMaili webhooki custom headerisse "X-Skene-Hook"
//
// AgentMaili konsool -> Webhooks -> uus:
//   URL    https://www.skene.info/api/agentmail-hook
//   Event  message.received.unauthenticated   (AINUS; see event on vaikimisi VALJAS ja
//          tuleb event_types-listi eraldi lisada -- neid kirju ei tule enam
//          message.received'ina)
//   Header X-Skene-Hook: <AGENTMAIL_HOOK_SECRET>
const crypto = require("crypto");

const API = "https://api.agentmail.to/v0";
const SILT = "unauthenticated";

// Ainult see postkast -- webhook on org-tasemel ja voib pohimotteliselt tuua ka teiste
// postkastide sundmusi.
const POSTKAST = "skene.info@agentmail.to";

// Saatjadomeenid, kelle puhul silt eemaldatakse. Alamdomeenid loevad kaasa
// (mail93.atl281.mcsv.net kuulub mcsv.net alla), aga From-aadress on
// info@kultuurivabrik.ee -- mcsv.net paistab ainult Message-ID-s.
const LUBATUD_SAATJAD = [
  "kultuurivabrik.ee",   // Paavli Kultuurivabrik, Mailchimp
  "rada7.ee",            // Rada7 uudiskiri
  "legendaarne.ee",      // Legendaarne mailinglist
  "web3forms.com"        // skene.info kontaktivorm
];

function saladusOk(req) {
  const oodatud = process.env.AGENTMAIL_HOOK_SECRET || "";
  const saadud = String(req.headers["x-skene-hook"] || "");
  if (!oodatud) return false;
  const a = Buffer.from(saadud), b = Buffer.from(oodatud);
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

// "Paavli Kultuurivabrik <info@kultuurivabrik.ee>" -> "kultuurivabrik.ee"
function domeen(from) {
  const s = String(from == null ? "" : from);
  const m = s.match(/<([^>]+)>/);
  const aadress = (m ? m[1] : s).trim().toLowerCase();
  const at = aadress.lastIndexOf("@");
  return at < 0 ? "" : aadress.slice(at + 1);
}

function lubatud(from) {
  const d = domeen(from);
  if (!d) return false;
  return LUBATUD_SAATJAD.some(function (x) { return d === x || d.endsWith("." + x); });
}

function safeJson(s) { try { return JSON.parse(s); } catch (e) { return {}; } }

module.exports = async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ ok: false, error: "method" });
  }
  if (!saladusOk(req)) return res.status(401).json({ ok: false, error: "auth" });

  const body = typeof req.body === "string" ? safeJson(req.body) : (req.body || {});
  if (body.event_type !== "message.received." + SILT) {
    // Vale event tellitud -- vastame 200, et Svix ei hakkaks kordama.
    return res.status(200).json({ ok: true, skip: "event" });
  }

  const msg = body.message || {};
  const inboxId = String(msg.inbox_id || "");
  const threadId = String(msg.thread_id || "");
  const from = msg.from;

  if (!inboxId || !threadId) return res.status(400).json({ ok: false, error: "payload" });
  if (inboxId !== POSTKAST) return res.status(200).json({ ok: true, skip: "postkast" });

  // Tundmatu saatja: silt JAAB alles. Kiri jaab konsooli karantiini, kust Silver saab
  // selle kasitsi vabastada, kui tegu on paris asjaga.
  if (!lubatud(from)) {
    console.log("agentmail-hook: tundmatu saatja, silt jaab", domeen(from), threadId);
    return res.status(200).json({ ok: true, skip: "saatja" });
  }

  const votme = process.env.AGENTMAIL_API_KEY || "";
  if (!votme) return res.status(500).json({ ok: false, error: "config" });

  const r = await fetch(
    API + "/inboxes/" + encodeURIComponent(inboxId) + "/threads/" + encodeURIComponent(threadId),
    {
      method: "PATCH",
      headers: { Authorization: "Bearer " + votme, "Content-Type": "application/json" },
      body: JSON.stringify({ remove_labels: [SILT] })
    }
  );

  if (!r.ok) {
    // 5xx -> Svix proovib uuesti. Just seda me tahame, kui AgentMaili API norgutab.
    console.error("agentmail-hook: PATCH ebaonnestus", r.status, threadId);
    return res.status(502).json({ ok: false, error: "agentmail", status: r.status });
  }

  console.log("agentmail-hook: silt eemaldatud", domeen(from), threadId);
  return res.status(200).json({ ok: true, thread_id: threadId });
};
