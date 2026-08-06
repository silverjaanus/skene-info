// Testib api/tagasiside.js loogikat ilma Vercelita ja ilma Upstashita:
// req/res on mokitud, globalThis.fetch teeskleb Upstashi REST-i (malusisene list).
process.env.KV_REST_API_URL = "https://fake.upstash.io";
process.env.KV_REST_API_TOKEN = "fake";
process.env.VIEW_SECRET = "SALAJANE-VOTI-1234567890";

const LIST = [];
const CNT = {};
globalThis.fetch = async (url, opt) => {
  const cmds = JSON.parse(opt.body);
  const out = cmds.map((c) => {
    const [op, key, ...rest] = c;
    if (op === "RPUSH") { LIST.push(rest[0]); return { result: LIST.length }; }
    if (op === "LTRIM") return { result: "OK" };
    if (op === "INCR") { CNT[key] = (CNT[key] || 0) + 1; return { result: CNT[key] }; }
    if (op === "EXPIRE") return { result: 1 };
    if (op === "LRANGE") return { result: LIST.slice() };
    return { result: null };
  });
  return { ok: true, status: 200, text: async () => JSON.stringify(out) };
};

const handler = require("../api/tagasiside.js");

function mk(method, body, query, headers) {
  const res = { _s: 200, _j: null, _h: {} };
  res.setHeader = (k, v) => { res._h[k] = v; };
  res.status = (s) => { res._s = s; return res; };
  res.json = (j) => { res._j = j; return res; };
  res.end = () => res;
  return [{ method, body, query: query || {}, headers: headers || { "x-forwarded-for": "1.2.3.4" } }, res];
}

let ok = 0, fail = 0;
function on(nimi, tingimus, lisa) {
  if (tingimus) { ok++; console.log("  OK   " + nimi); }
  else { fail++; console.log("  VIGA " + nimi + (lisa ? "  -> " + JSON.stringify(lisa) : "")); }
}

(async () => {
  console.log("POST valideerimine:");
  let [q, r] = mk("POST", { a: {}, txt: "" }); await handler(q, r);
  on("tyhi vastus -> 400", r._s === 400 && r._j.error === "tyhi", r._j);

  [q, r] = mk("POST", { a: { miks: ["x"] }, hp: "bot" }); await handler(q, r);
  on("honeypot -> vaikne ok, midagi ei salvestata", r._s === 200 && r._j.ok && LIST.length === 0);

  [q, r] = mk("POST", { a: { tihedus: "kuus" }, email: "vale-aadress" }); await handler(q, r);
  on("katkine email -> 400", r._s === 400 && r._j.error === "email", r._j);

  [q, r] = mk("POST", {
    a: { miks: ["konkreetne", "reliisid"], tihedus: "kuus" },
    txt: "  ruumi ees ja taga  ", email: "  TEST@Naide.EE ", sait: "klubi", lang: "en", v: 1
  }); await handler(q, r);
  on("korralik vastus -> 200", r._s === 200 && r._j.ok, r._j);
  const k = JSON.parse(LIST[0] || "{}");
  on("email normaliseeritud", k.email === "test@naide.ee", k.email);
  on("txt trimmitud", k.txt === "ruumi ees ja taga", k.txt);
  on("sait ja lang sailisid", k.sait === "klubi" && k.lang === "en", k);
  on("ts on ISO", /^\d{4}-\d\d-\d\dT/.test(k.ts || ""), k.ts);

  [q, r] = mk("POST", { a: { miks: "<script>x</script>".repeat(20) } }); await handler(q, r);
  const k2 = JSON.parse(LIST[LIST.length - 1]);
  on("liiga pikk vaartus loigatakse 64 margini", k2.a.miks.length === 64, k2.a.miks.length);

  [q, r] = mk("POST", { a: { "halb-v6ti!": "x", ok_key: "y" } }); await handler(q, r);
  const k3 = JSON.parse(LIST[LIST.length - 1]);
  on("votmed puhastatakse", !("halb-v6ti!" in k3.a) && k3.a.ok_key === "y", k3.a);

  [q, r] = mk("POST", { a: { x: new Array(40).fill("v") } }); await handler(q, r);
  const k4 = JSON.parse(LIST[LIST.length - 1]);
  on("massiiv piiratakse 12 elemendile", k4.a.x.length === 12, k4.a.x.length);

  // NB: eelnevad 400/honeypot-vastused EI joua INCR-ini (valideerimine on enne),
  // seega IP 1.2.3.4 on siin punktis kasutanud 4 katset 5-st.
  console.log("\nPaevalimiit (5/paev sama IP):");
  const enne = LIST.length;
  let viimane = null;
  for (let i = 0; i < 4; i++) { [q, r] = mk("POST", { a: { tihedus: "kuus" } }); await handler(q, r); viimane = r; }
  on("ule limiidi -> 429", viimane._s === 429 && viimane._j.error === "liiga_palju", viimane._j);
  on("mahub veel tapselt 1 (kokku 5/paev)", LIST.length === enne + 1, { enne, nyyd: LIST.length });

  [q, r] = mk("POST", { a: { tihedus: "kuus" } }, {}, { "x-forwarded-for": "9.9.9.9" }); await handler(q, r);
  on("teine IP saab ikka saata", r._s === 200 && r._j.ok, r._j);

  console.log("\nGET (vaade):");
  [q, r] = mk("GET", null, { t: "vale" }); await handler(q, r);
  on("vale voti -> 403", r._s === 403 && r._j.error === "auth", r._j);

  [q, r] = mk("GET", null, { t: "" }); await handler(q, r);
  on("tyhi voti -> 403", r._s === 403);

  [q, r] = mk("GET", null, { t: process.env.VIEW_SECRET }); await handler(q, r);
  on("oige voti -> 200 + kirjed", r._s === 200 && r._j.ok && r._j.n === LIST.length, { n: r._j && r._j.n, list: LIST.length });

  console.log("\nCORS ja meetodid:");
  [q, r] = mk("OPTIONS", null, {}, { origin: "https://klubi.skene.info", "x-forwarded-for": "1.1.1.1" });
  await handler(q, r);
  on("OPTIONS -> 204 + lubatud origin", r._s === 204 && r._h["Access-Control-Allow-Origin"] === "https://klubi.skene.info", r._h);

  [q, r] = mk("POST", { a: { tihedus: "kuus" } }, {}, { origin: "https://kuri.example.com", "x-forwarded-for": "2.2.2.2" });
  await handler(q, r);
  on("voora origin'i puhul CORS-paist ei anta", !r._h["Access-Control-Allow-Origin"], r._h);

  [q, r] = mk("PUT", {}); await handler(q, r);
  on("PUT -> 405", r._s === 405);

  console.log("\nPuuduv seadistus:");
  const u = process.env.KV_REST_API_URL; delete process.env.KV_REST_API_URL;
  [q, r] = mk("POST", { a: { tihedus: "kuus" } }, {}, { "x-forwarded-for": "3.3.3.3" }); await handler(q, r);
  on("ilma Redise seadistuseta -> 500 config", r._s === 500 && r._j.error === "config", r._j);
  process.env.KV_REST_API_URL = u;

  console.log("\n" + ok + " OK, " + fail + " VIGA");
  process.exit(fail ? 1 : 0);
})();
