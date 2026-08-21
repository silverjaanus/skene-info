// node scripts/test_agentmail_hook.js  (jookseb ka CI-s, checks.yml)
//
// Valvab api/agentmail-hook.js't. Kriitiline osa on SAATJAKONTROLL: kui see katki laheb,
// hakkab endpoint vabastama karantiinist suvalisi voltsitud saatjaid otse sinna postkasti,
// kust Claude sisu kaevandab. Ei kutsu AgentMaili API-t -- global fetch on mockitud.
process.env.AGENTMAIL_HOOK_SECRET = "test-saladus-1234567890";
process.env.AGENTMAIL_API_KEY = "test-key";

let viimaneFetch = null;
global.fetch = async function (url, opts) {
  viimaneFetch = { url: url, opts: opts };
  return { ok: true, status: 200 };
};

const handler = require("../api/agentmail-hook.js");

function res() {
  const o = { code: 0, body: null, headers: {} };
  o.setHeader = function (k, v) { o.headers[k] = v; return o; };
  o.status = function (c) { o.code = c; return o; };
  o.json = function (b) { o.body = b; return o; };
  o.end = function () { return o; };
  return o;
}

function req(opts) {
  return {
    method: opts.method || "POST",
    headers: opts.headers || { "x-skene-hook": "test-saladus-1234567890" },
    body: opts.body
  };
}

function payload(from, inbox) {
  return {
    event_type: "message.received.unauthenticated",
    event_id: "evt_1",
    message: {
      inbox_id: inbox || "skene.info@agentmail.to",
      thread_id: "03ef8850-ffc5-4810-9f2b-27f1c6ba7587",
      message_id: "<x@mail93.atl281.mcsv.net>",
      from: from
    }
  };
}

let vigu = 0;
function ok(nimi, tingimus, lisa) {
  if (tingimus) { console.log("  OK   " + nimi); }
  else { vigu++; console.log("  VIGA " + nimi + (lisa ? "  -> " + JSON.stringify(lisa) : "")); }
}

(async function () {
  let r;

  r = res(); await handler(req({ method: "GET" }), r);
  ok("GET -> 405", r.code === 405, r.body);

  r = res(); await handler(req({ headers: { "x-skene-hook": "vale" }, body: payload("info@kultuurivabrik.ee") }), r);
  ok("vale saladus -> 401", r.code === 401, r.body);

  r = res(); await handler(req({ headers: {}, body: payload("info@kultuurivabrik.ee") }), r);
  ok("saladus puudu -> 401", r.code === 401, r.body);

  r = res(); await handler(req({ body: { event_type: "message.received", message: {} } }), r);
  ok("vale event -> 200 skip:event", r.code === 200 && r.body.skip === "event", r.body);

  r = res(); await handler(req({ body: payload("info@kultuurivabrik.ee", "muu@agentmail.to") }), r);
  ok("vale postkast -> 200 skip:postkast", r.code === 200 && r.body.skip === "postkast", r.body);

  viimaneFetch = null;
  r = res(); await handler(req({ body: payload("spam@kurjategija.ru") }), r);
  ok("tundmatu saatja -> 200 skip:saatja", r.code === 200 && r.body.skip === "saatja", r.body);
  ok("tundmatu saatja -> API-t EI kutsutud", viimaneFetch === null);

  // Sarnane, aga mitte sama domeen -- ei tohi labi lasta.
  r = res(); await handler(req({ body: payload("info@kultuurivabrik.ee.evil.com") }), r);
  ok("libadomeen -> 200 skip:saatja", r.code === 200 && r.body.skip === "saatja", r.body);

  viimaneFetch = null;
  r = res(); await handler(req({ body: payload("Paavli Kultuurivabrik <info@kultuurivabrik.ee>") }), r);
  ok("tuntud saatja (Display Name) -> 200 ok", r.code === 200 && r.body.ok === true, r.body);
  ok("PATCH oige URL", viimaneFetch && viimaneFetch.url ===
    "https://api.agentmail.to/v0/inboxes/skene.info%40agentmail.to/threads/03ef8850-ffc5-4810-9f2b-27f1c6ba7587",
    viimaneFetch && viimaneFetch.url);
  ok("PATCH meetod + body", viimaneFetch && viimaneFetch.opts.method === "PATCH" &&
    viimaneFetch.opts.body === '{"remove_labels":["unauthenticated"]}',
    viimaneFetch && viimaneFetch.opts.body);

  r = res(); await handler(req({ body: payload("uudiskiri@rada7.ee") }), r);
  ok("rada7 -> 200 ok", r.code === 200 && r.body.ok === true, r.body);

  r = res(); await handler(req({ body: payload("notify+5f3c9r@web3forms.com") }), r);
  ok("web3forms -> 200 ok", r.code === 200 && r.body.ok === true, r.body);

  // JSON stringina (kui Vercel body't ei parsi)
  r = res(); await handler(req({ body: JSON.stringify(payload("info@kultuurivabrik.ee")) }), r);
  ok("body stringina -> 200 ok", r.code === 200 && r.body.ok === true, r.body);

  // AgentMaili API viga -> 502, et Svix kordaks
  global.fetch = async function () { return { ok: false, status: 500 }; };
  r = res(); await handler(req({ body: payload("info@kultuurivabrik.ee") }), r);
  ok("AgentMail 500 -> 502", r.code === 502, r.body);

  console.log(vigu === 0 ? "\nKOIK TESTID LABITUD" : "\n" + vigu + " VIGA");
  process.exit(vigu === 0 ? 0 : 1);
})();
