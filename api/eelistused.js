// api/eelistused.js -- skene.info uudiskirja eelistuste API (MailerLite)
//
// GET  /api/eelistused?e=<email>&t=<tok>          -> {ok,email,lang,status,groups:[...]}
// POST /api/eelistused  {e,t,groups:["metal",..]} -> {ok,email,lang,status,groups:[...]}
//
// Turve: tok = HMAC-SHA256(PREF_SECRET, lowercase(email)) esimesed 16 hex-marki.
// Sama arvutus on scripts/ml_sync_groups.py-s, mis kirjutab vaartuse ML kliendivaljale;
// kirjas on link ?e={$email}&t={$tok}. Ilma kehtiva tok-ita 403.
//
// Vercel env (Production + Preview): ML_TOKEN, PREF_SECRET
const crypto = require("crypto");

const API = "https://connect.mailerlite.com/api";

// HOIA SUNKROONIS mailerlite_config.json "groups"-plokiga
const GROUPS = {
  metal: "192538281421833701",
  rap: "192956907302946513",
  klubi: "192956907404658437"
};
const CATS = Object.keys(GROUPS);
const ID2CAT = {};
for (const c of CATS) ID2CAT[GROUPS[c]] = c;

function tokenFor(email) {
  return crypto.createHmac("sha256", process.env.PREF_SECRET || "")
    .update(email).digest("hex").slice(0, 16);
}

function verify(email, tok) {
  if (!email || !tok || !process.env.PREF_SECRET) return false;
  const a = Buffer.from(String(tok).trim().toLowerCase());
  const b = Buffer.from(tokenFor(email));
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

async function ml(method, path, body) {
  const headers = {
    Authorization: "Bearer " + (process.env.ML_TOKEN || ""),
    Accept: "application/json"
  };
  if (body) headers["Content-Type"] = "application/json";
  const r = await fetch(API + path, {
    method: method,
    headers: headers,
    body: body ? JSON.stringify(body) : undefined
  });
  const txt = await r.text();
  let data = null;
  if (txt) { try { data = JSON.parse(txt); } catch (e) { data = null; } }
  return { status: r.status, data: data };
}

function safeJson(s) { try { return JSON.parse(s); } catch (e) { return {}; } }

module.exports = async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  const isPost = req.method === "POST";
  if (!isPost && req.method !== "GET") {
    res.setHeader("Allow", "GET, POST");
    return res.status(405).json({ ok: false, error: "method" });
  }
  if (!process.env.ML_TOKEN || !process.env.PREF_SECRET) {
    return res.status(500).json({ ok: false, error: "config" });
  }
  const body = isPost
    ? (typeof req.body === "string" ? safeJson(req.body) : (req.body || {}))
    : {};
  const q = req.query || {};
  const email = String((isPost ? body.e : q.e) || "").trim().toLowerCase();
  const tok = String((isPost ? body.t : q.t) || "").trim();
  if (!verify(email, tok)) return res.status(403).json({ ok: false, error: "auth" });

  const sub = await ml("GET", "/subscribers/" + encodeURIComponent(email));
  if (sub.status === 404) return res.status(404).json({ ok: false, error: "notfound" });
  if (sub.status >= 300 || !sub.data || !sub.data.data) {
    return res.status(502).json({ ok: false, error: "ml", status: sub.status });
  }
  const s = sub.data.data;
  const fields = s.fields || {};
  const lang = fields.keel === "en" ? "en" : "et";
  const cur = new Set();
  for (const g of (s.groups || [])) {
    const c = ID2CAT[String(g.id)];
    if (c) cur.add(c);
  }
  const out = { ok: true, email: email, lang: lang, status: s.status || "active" };

  if (!isPost) {
    out.groups = CATS.filter(function (c) { return cur.has(c); });
    return res.status(200).json(out);
  }

  if (!Array.isArray(body.groups)) {
    return res.status(400).json({ ok: false, error: "groups", message: "groups peab olema massiiv, nt {\"groups\":[\"metal\"]}" });
  }
  const wanted = body.groups.map(String);
  const want = new Set(wanted.filter(function (c) { return CATS.indexOf(c) >= 0; }));
  const failed = [];
  for (const c of CATS) {
    const path = "/subscribers/" + s.id + "/groups/" + GROUPS[c];
    if (want.has(c) && !cur.has(c)) {
      const r = await ml("POST", path);
      if (r.status >= 300) failed.push(c);
    } else if (!want.has(c) && cur.has(c)) {
      const r = await ml("DELETE", path);
      if (r.status >= 300) failed.push(c);
    }
  }
  if (failed.length) return res.status(502).json({ ok: false, error: "ml", failed: failed });
  out.groups = CATS.filter(function (c) { return want.has(c); });
  return res.status(200).json(out);
};
