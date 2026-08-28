// api/dash.js -- skene.info kaugjuhtimispaneeli (dash) API. Upstash Redis REST,
// sama muster mis api/tagasiside.js (POLE npm-teeke, puhas fetch).
//
// GET  /api/dash?t=SECRET&mode=status          -> kogu seis dashboardile
// GET  /api/dash?t=SECRET&mode=poll            -> kerge seis pollerile (queue+kaimas+vastused)
// GET  /api/dash?t=SECRET&mode=uudiskiri&lang=et|en -> {ok, html} (eraldi, sest suur)
// POST /api/dash {t, action, ...}              -> tegevused (vt switch all)
//
// Verceli env: DASH_SECRET (kohustuslik; sama väärtus repo lokaalses .env-is, et
// sweep/poller saaks API-t kutsuda), DASH_GH_PAT (valikuline, AINULT Andmekorje
// workflow_dispatch'iks; fine-grained PAT, ainult see repo, Actions read+write),
// MAILERLITE_TOKEN (valikuline, ainult kampaaniastatistika lugemiseks).
// Upstash: samad KV_REST_API_* / UPSTASH_REDIS_REST_* mis tagasisidel.
const crypto = require("crypto");

const P = "skene:dash:";           // Redis võtmeprefiks
const REPO = "silverjaanus/skene-info";
const LOG_MAX = 40;                // sündmuste logi pikkus

function env(a, b) { return process.env[a] || process.env[b] || ""; }

async function redis(commands) {
  const url = env("KV_REST_API_URL", "UPSTASH_REDIS_REST_URL");
  const tok = env("KV_REST_API_TOKEN", "UPSTASH_REDIS_REST_TOKEN");
  if (!url || !tok) return { ok: false, error: "config: Upstash env puudub" };
  const r = await fetch(url.replace(/\/+$/, "") + "/pipeline", {
    method: "POST",
    headers: { Authorization: "Bearer " + tok, "Content-Type": "application/json" },
    body: JSON.stringify(commands)
  });
  const txt = await r.text();
  let data = null;
  try { data = JSON.parse(txt); } catch (e) { data = null; }
  if (!r.ok || !Array.isArray(data)) return { ok: false, error: "redis", status: r.status };
  return { ok: true, data: data };
}

function tokenOk(t) {
  const secret = process.env.DASH_SECRET || "";
  if (!secret || !t) return false;
  const a = Buffer.from(String(t)), b = Buffer.from(secret);
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

function j(s, fallback) { try { const v = JSON.parse(s); return v == null ? fallback : v; } catch (e) { return fallback; } }
function cut(s, n) { return String(s == null ? "" : s).slice(0, n); }
function nyyd() { return new Date().toISOString(); }
function uusId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }

// --- mitu võtit korraga: GET-id ühes pipeline'is ---
async function loeVotmed(nimed) {
  const res = await redis(nimed.map(function (n) { return ["GET", P + n]; }));
  if (!res.ok) return null;
  const out = {};
  nimed.forEach(function (n, i) { out[n] = (res.data[i] || {}).result || null; });
  return out;
}

async function salvesta(nimi, vaartus) {
  return redis([["SET", P + nimi, JSON.stringify(vaartus)]]);
}

async function logi(mis) {
  const k = await loeVotmed(["log"]);
  const list = k ? j(k.log, []) : [];
  list.unshift({ aeg: nyyd(), mis: cut(mis, 300) });
  await salvesta("log", list.slice(0, LOG_MAX));
}

// --- GitHub Actions seis (avalik repo, autentimata; talub tõrget) ---
async function actionsSeis() {
  async function yks(wf) {
    try {
      const r = await fetch("https://api.github.com/repos/" + REPO +
        "/actions/workflows/" + wf + "/runs?per_page=1", {
        headers: { "User-Agent": "skene-dash", Accept: "application/vnd.github+json" }
      });
      if (!r.ok) return { wf: wf, viga: "HTTP " + r.status };
      const d = await r.json();
      const run = (d.workflow_runs || [])[0];
      if (!run) return { wf: wf, viga: "jookse pole" };
      return { wf: wf, status: run.status, conclusion: run.conclusion,
               aeg: run.updated_at, url: run.html_url, nimi: run.name };
    } catch (e) { return { wf: wf, viga: cut(e.message, 80) }; }
  }
  const both = await Promise.all([yks("update.yml"), yks("checks.yml")]);
  return { andmekorje: both[0], kontrollid: both[1] };
}

// --- MailerLite viimase saadetud kampaania statistika (valikuline) ---
async function mlSeis() {
  const tok = process.env.MAILERLITE_TOKEN || "";
  if (!tok) return { viga: "MAILERLITE_TOKEN env puudub (valikuline)" };
  try {
    const r = await fetch("https://connect.mailerlite.com/api/campaigns?filter[status]=sent&limit=4", {
      headers: { Authorization: "Bearer " + tok, Accept: "application/json" }
    });
    if (!r.ok) return { viga: "ML HTTP " + r.status };
    const d = await r.json();
    return { kampaaniad: (d.data || []).map(function (c) {
      const s = c.stats || {};
      return { nimi: c.name, saadetud: c.finished_at,
               saajaid: s.sent, avamisi: s.unique_opens_count, avamisprotsent: (s.open_rate||{}).string,
               klikke: s.clicks_count, klikiprotsent: (s.click_rate||{}).string };
    }) };
  } catch (e) { return { viga: cut(e.message, 80) }; }
}

// --- Andmekorje käsitsi käivitus (workflow_dispatch; vajab DASH_GH_PAT) ---
async function dispatchAndmekorje() {
  const pat = process.env.DASH_GH_PAT || "";
  if (!pat) return { ok: false, error: "DASH_GH_PAT env puudub — lisa Vercelisse (vt PROJEKT.md 5D)" };
  const r = await fetch("https://api.github.com/repos/" + REPO +
    "/actions/workflows/update.yml/dispatches", {
    method: "POST",
    headers: { "User-Agent": "skene-dash", Accept: "application/vnd.github+json",
               Authorization: "Bearer " + pat, "Content-Type": "application/json" },
    body: JSON.stringify({ ref: "main" })
  });
  if (r.status === 204) return { ok: true };
  return { ok: false, error: "GitHub HTTP " + r.status + " " + cut(await r.text(), 200) };
}

module.exports = async function (req, res) {
  res.setHeader("Cache-Control", "no-store");
  // Sama origin (www) — CORS-i pole vaja; localhost testiks siiski lubatud.
  const o = String(req.headers.origin || "");
  if (/^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(o)) {
    res.setHeader("Access-Control-Allow-Origin", o);
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  }
  if (req.method === "OPTIONS") { res.statusCode = 204; return res.end(); }

  const q = req.query || {};
  const body = (req.method === "POST") ? (typeof req.body === "object" && req.body ? req.body
    : j(req.body, {})) : {};
  if (!tokenOk(q.t || body.t)) {
    res.statusCode = 401;
    return res.end(JSON.stringify({ ok: false, error: process.env.DASH_SECRET ? "vale token" : "config: DASH_SECRET env puudub" }));
  }

  try {
    if (req.method === "GET") {
      const mode = String(q.mode || "status");
      if (mode === "uudiskiri") {
        const lang = q.lang === "en" ? "en" : "et";
        const k = await loeVotmed(["uudiskiri_" + lang]);
        const v = k ? j(k["uudiskiri_" + lang], null) : null;
        return res.end(JSON.stringify({ ok: true, html: v && v.html || "", aeg: v && v.aeg || null }));
      }
      if (mode === "poll") {
        const k = await loeVotmed(["queue", "kaimas", "vastused"]);
        if (!k) return res.end(JSON.stringify({ ok: false, error: "redis" }));
        return res.end(JSON.stringify({ ok: true, queue: j(k.queue, []),
          kaimas: j(k.kaimas, null),
          vastused: j(k.vastused, []).filter(function (v) { return !v.toodeldud; }) }));
      }
      // mode=status — kõik peale uudiskirja HTML-i
      const k = await loeVotmed(["queue", "kaimas", "seis", "otsused", "vastused", "log"]);
      if (!k) return res.end(JSON.stringify({ ok: false, error: "redis (Upstash env puudub?)" }));
      const lisad = await Promise.all([actionsSeis(), mlSeis()]);
      return res.end(JSON.stringify({ ok: true,
        queue: j(k.queue, []), kaimas: j(k.kaimas, null), seis: j(k.seis, null),
        otsused: j(k.otsused, []), vastused: j(k.vastused, []), log: j(k.log, []),
        actions: lisad[0], mailerlite: lisad[1], aeg: nyyd() }));
    }

    // ---- POST ----
    const a = String(body.action || "");
    if (a === "lisa_job") {
      const tyyp = ["sweep", "postkast", "markus"].indexOf(body.tyyp) >= 0 ? body.tyyp : null;
      if (!tyyp) return res.end(JSON.stringify({ ok: false, error: "tundmatu tyyp" }));
      const k = await loeVotmed(["queue"]);
      const queue = k ? j(k.queue, []) : [];
      if (queue.length >= 10) return res.end(JSON.stringify({ ok: false, error: "queue täis" }));
      // sama tüübi duplikaat (v.a märkus) — ära lisa teist korda
      if (tyyp !== "markus" && queue.some(function (x) { return x.tyyp === tyyp; }))
        return res.end(JSON.stringify({ ok: false, error: "sama job on juba ootel" }));
      const job = { id: uusId(), tyyp: tyyp, full: body.full ? 1 : 0,
                    markus: cut(body.markus, 2000), loodud: nyyd() };
      queue.push(job);
      await salvesta("queue", queue);
      await logi("Uus job dashilt: " + tyyp + (job.full ? " (FULL)" : "") +
                 (job.markus ? " — " + cut(job.markus, 60) : ""));
      return res.end(JSON.stringify({ ok: true, job: job }));
    }
    if (a === "tyhista_job") {
      const k = await loeVotmed(["queue"]);
      const queue = (k ? j(k.queue, []) : []).filter(function (x) { return x.id !== body.id; });
      await salvesta("queue", queue);
      await logi("Job tühistatud: " + cut(body.id, 20));
      return res.end(JSON.stringify({ ok: true, queue: queue }));
    }
    if (a === "vota_job") {
      const k = await loeVotmed(["queue"]);
      const queue = k ? j(k.queue, []) : [];
      const i = queue.findIndex(function (x) { return x.id === body.id; });
      if (i < 0) return res.end(JSON.stringify({ ok: false, error: "jobi pole (juba võetud?)" }));
      const job = queue.splice(i, 1)[0];
      await salvesta("queue", queue);
      await salvesta("kaimas", { job: job, algus: nyyd() });
      await logi("Job võetud töösse: " + job.tyyp + (job.full ? " (FULL)" : ""));
      return res.end(JSON.stringify({ ok: true, job: job }));
    }
    if (a === "job_valmis") {
      await salvesta("kaimas", null);
      await logi("Job valmis: " + cut(body.id, 20) + (body.note ? " — " + cut(body.note, 200) : ""));
      return res.end(JSON.stringify({ ok: true }));
    }
    if (a === "vasta_otsus") {
      if (!body.oid || !body.valik) return res.end(JSON.stringify({ ok: false, error: "oid+valik vaja" }));
      const k = await loeVotmed(["vastused"]);
      const list = k ? j(k.vastused, []) : [];
      // sama otsuse vana vastus asendatakse (kuni pole töödeldud)
      const jarel = list.filter(function (v) { return !(v.oid === body.oid && !v.toodeldud); });
      jarel.push({ oid: cut(body.oid, 40), valik: cut(body.valik, 40),
                   markus: cut(body.markus, 1000), aeg: nyyd(), toodeldud: 0 });
      await salvesta("vastused", jarel.slice(-50));
      await logi("Otsusele vastatud: " + body.oid + " → " + body.valik);
      return res.end(JSON.stringify({ ok: true }));
    }
    if (a === "vastus_toodeldud") {
      const k = await loeVotmed(["vastused"]);
      const list = (k ? j(k.vastused, []) : []).map(function (v) {
        if (v.oid === body.oid) v.toodeldud = 1;
        return v;
      });
      await salvesta("vastused", list);
      return res.end(JSON.stringify({ ok: true }));
    }
    if (a === "set_otsused") {
      if (!Array.isArray(body.otsused)) return res.end(JSON.stringify({ ok: false, error: "otsused peab olema massiiv" }));
      await salvesta("otsused", body.otsused.slice(0, 30));
      await logi("Otsustuspunktid uuendatud: " + body.otsused.length + " tk");
      return res.end(JSON.stringify({ ok: true }));
    }
    if (a === "set_seis") {
      if (!body.seis || typeof body.seis !== "object") return res.end(JSON.stringify({ ok: false, error: "seis puudub" }));
      body.seis.push_aeg = nyyd();
      await salvesta("seis", body.seis);
      return res.end(JSON.stringify({ ok: true }));
    }
    if (a === "set_uudiskiri") {
      if (body.et) await salvesta("uudiskiri_et", { html: cut(body.et, 400000), aeg: nyyd() });
      if (body.en) await salvesta("uudiskiri_en", { html: cut(body.en, 400000), aeg: nyyd() });
      return res.end(JSON.stringify({ ok: true }));
    }
    if (a === "dispatch") {
      const r = await dispatchAndmekorje();
      if (r.ok) await logi("Andmekorje käivitatud dashilt (workflow_dispatch)");
      return res.end(JSON.stringify(r));
    }
    res.statusCode = 400;
    return res.end(JSON.stringify({ ok: false, error: "tundmatu action" }));
  } catch (e) {
    res.statusCode = 500;
    return res.end(JSON.stringify({ ok: false, error: cut(e && e.message, 200) }));
  }
};
