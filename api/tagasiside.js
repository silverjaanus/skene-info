// api/tagasiside.js -- skene.info tagasisidevormi API (Upstash Redis REST)
//
// POST /api/tagasiside   {sait,lang,a:{...},txt,email,hp}  -> {ok:true}
// GET  /api/tagasiside?t=<VIEW_SECRET>                     -> {ok,n,entries:[...]}
//
// MIKS Upstash REST, mitte npm-teek: repos POLE package.json'i ega node_modules'it
// (staatiline sait). REST-liidesega saab hakkama puhta fetch'iga, uut ehitussammu
// ei teki. Sama pohjus, miks siin pole @vercel/blob'i ega muud SDK-d.
//
// Vercel env (Production + Preview), 3 tukki:
//   KV_REST_API_URL    voi UPSTASH_REDIS_REST_URL     <- Upstashi integratsioon paneb ise
//   KV_REST_API_TOKEN  voi UPSTASH_REDIS_REST_TOKEN   <- sama
//   VIEW_SECRET        <- ise valitud pikk juhuslik sone, tagasiside-vaate parool
const crypto = require("crypto");

const KEY = "skene:tagasiside";
const MAX = 5000;          // kui palju vastuseid alles hoiame
const RL_PAEVAS = 5;       // sama IP kohta paevas

// Alamdomeenid on eraldi origin'id ja vercel.json host-route suunab neil /api/* oma
// kausta (-> 404), seega vorm postitab ALATI www-le. Sellepara on CORS kohustuslik.
const LUBATUD = [
  "https://www.skene.info",
  "https://skene.info",
  "https://rap.skene.info",
  "https://klubi.skene.info",
  "http://127.0.0.1:8877",
  "http://localhost:8877"
];

function env(a, b) { return process.env[a] || process.env[b] || ""; }

async function redis(commands) {
  const url = env("KV_REST_API_URL", "UPSTASH_REDIS_REST_URL");
  const tok = env("KV_REST_API_TOKEN", "UPSTASH_REDIS_REST_TOKEN");
  if (!url || !tok) return { ok: false, error: "config" };
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

function ipHash(req) {
  const ip = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim() || "?";
  // Toorest IP-d EI salvestata kuhugi - ainult sool + hash, ainult paevaseks loenduriks.
  return crypto.createHmac("sha256", process.env.VIEW_SECRET || "s")
    .update(ip).digest("hex").slice(0, 12);
}

function safeJson(s) { try { return JSON.parse(s); } catch (e) { return {}; } }

function cut(s, n) { return String(s == null ? "" : s).slice(0, n); }

// Kusimused elavad data/tagasiside-kysimused.json'is, MITTE siin. Seetottu on valideerimine
// uldine (kuju ja pikkused), mitte kusimusepohine - nii saab kusimusi muuta ilma koodita.
function puhastaVastused(a) {
  if (!a || typeof a !== "object" || Array.isArray(a)) return null;
  const out = {};
  let n = 0;
  for (const k of Object.keys(a)) {
    if (++n > 12) break;
    const kk = cut(k, 24).replace(/[^a-z0-9_]/gi, "");
    if (!kk) continue;
    const v = a[k];
    if (Array.isArray(v)) {
      out[kk] = v.slice(0, 12).map(function (x) { return cut(x, 64); }).filter(Boolean);
    } else if (typeof v === "string" || typeof v === "number") {
      out[kk] = cut(v, 64);
    }
  }
  return out;
}

function cors(req, res) {
  const o = String(req.headers.origin || "");
  if (LUBATUD.indexOf(o) >= 0) {
    res.setHeader("Access-Control-Allow-Origin", o);
    res.setHeader("Vary", "Origin");
  }
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Access-Control-Max-Age", "86400");
}

module.exports = async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  cors(req, res);
  if (req.method === "OPTIONS") return res.status(204).end();

  // ---------- LUGEMINE (tagasiside-vaade.html) ----------
  if (req.method === "GET") {
    const secret = process.env.VIEW_SECRET || "";
    const tok = String((req.query && req.query.t) || "");
    const a = Buffer.from(tok), b = Buffer.from(secret);
    if (!secret || a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
      return res.status(403).json({ ok: false, error: "auth" });
    }
    const r = await redis([["LRANGE", KEY, 0, -1]]);
    if (!r.ok) return res.status(r.error === "config" ? 500 : 502).json({ ok: false, error: r.error });
    const raw = (r.data[0] && r.data[0].result) || [];
    const entries = raw.map(safeJson).filter(function (x) { return x && x.ts; });
    return res.status(200).json({ ok: true, n: entries.length, entries: entries });
  }

  if (req.method !== "POST") {
    res.setHeader("Allow", "GET, POST, OPTIONS");
    return res.status(405).json({ ok: false, error: "method" });
  }

  // ---------- KIRJUTAMINE (tagasiside.html) ----------
  const body = typeof req.body === "string" ? safeJson(req.body) : (req.body || {});
  if (body.hp) return res.status(200).json({ ok: true });        // honeypot: vaikne "ok"

  const a = puhastaVastused(body.a);
  const txt = cut(body.txt, 2000).trim();
  if (!a || (!Object.keys(a).length && !txt)) {
    return res.status(400).json({ ok: false, error: "tyhi" });
  }
  const email = cut(body.email, 120).trim().toLowerCase();
  if (email && !/^[^@\s]+@[^@\s.]+\.[^@\s]+$/.test(email)) {
    return res.status(400).json({ ok: false, error: "email" });
  }

  const rlKey = KEY + ":rl:" + new Date().toISOString().slice(0, 10) + ":" + ipHash(req);
  const rl = await redis([["INCR", rlKey], ["EXPIRE", rlKey, 86400]]);
  if (!rl.ok) return res.status(rl.error === "config" ? 500 : 502).json({ ok: false, error: rl.error });
  if (Number((rl.data[0] && rl.data[0].result) || 0) > RL_PAEVAS) {
    return res.status(429).json({ ok: false, error: "liiga_palju" });
  }

  const kirje = {
    ts: new Date().toISOString(),
    sait: ["www", "rap", "klubi"].indexOf(body.sait) >= 0 ? body.sait : "www",
    lang: body.lang === "en" ? "en" : "et",
    v: Number(body.v) || 1,
    a: a
  };
  if (txt) kirje.txt = txt;
  if (email) kirje.email = email;

  const w = await redis([["RPUSH", KEY, JSON.stringify(kirje)], ["LTRIM", KEY, -MAX, -1]]);
  if (!w.ok) return res.status(502).json({ ok: false, error: w.error });
  return res.status(200).json({ ok: true });
};
