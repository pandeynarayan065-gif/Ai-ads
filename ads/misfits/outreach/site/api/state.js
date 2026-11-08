// Shared state for the Misfits lead board (Vercel serverless function, no dependencies).
// Storage: Upstash Redis REST (added from the Vercel Marketplace; it sets KV_REST_API_URL / KV_REST_API_TOKEN).
// Keys: mf:claim:<id> = {"by","at"} (set with NX, so only one person can hold a lead)
//       mf:lead:<id>  = {"status","next_followup","notes","updatedBy","updatedAt"}
// Every request needs the team passcode (env TEAM_CODE) in the x-team-code header.
//
// POST /api/state {action:"read", ids:[...]}                 -> {state:{id:{...lead, claim}}}
// POST /api/state {action:"claim", id, name}                 -> {ok:true} | {ok:false, claim}
// POST /api/state {action:"release", id, name}               -> {ok:true} | {ok:false, claim}
// POST /api/state {action:"update", id, name, patch}         -> {ok:true, lead} | {ok:false, claim}

const URL_ = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const TOKEN = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
const CODE = process.env.TEAM_CODE || "";
const FIELDS = ["status", "next_followup", "notes"];
const STATUSES = new Set(["new", "contacted", "followup", "replied", "call", "won", "no"]);

async function redis(cmds) {
  const r = await fetch(`${URL_}/pipeline`, {
    method: "POST", headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify(cmds),
  });
  if (!r.ok) throw new Error(`redis ${r.status}`);
  return (await r.json()).map((x) => { if (x.error) throw new Error(x.error); return x.result; });
}
const parse = (s) => { try { return s ? JSON.parse(s) : null; } catch { return null; } };
const cleanId = (id) => (typeof id === "string" && /^[a-z0-9-]{1,80}$/.test(id) ? id : null);
const cleanName = (n) => (typeof n === "string" ? n.trim().slice(0, 40) : "");

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  if (!URL_ || !TOKEN) return res.status(503).json({ error: "not_connected" });
  if (!CODE || req.headers["x-team-code"] !== CODE) return res.status(401).json({ error: "bad_code" });
  if (req.method !== "POST") return res.status(405).json({ error: "post_only" });
  const b = typeof req.body === "string" ? parse(req.body) || {} : req.body || {};
  try {
    if (b.action === "read") {
      const ids = (Array.isArray(b.ids) ? b.ids : []).map(cleanId).filter(Boolean).slice(0, 2000);
      if (!ids.length) return res.json({ state: {} });
      const [leads, claims] = await redis([["MGET", ...ids.map((i) => `mf:lead:${i}`)], ["MGET", ...ids.map((i) => `mf:claim:${i}`)]]);
      const state = {};
      ids.forEach((id, k) => {
        const l = parse(leads[k]), c = parse(claims[k]);
        if (l || c) state[id] = { ...(l || {}), claim: c };
      });
      return res.json({ state });
    }
    const id = cleanId(b.id), name = cleanName(b.name);
    if (!id || !name) return res.status(400).json({ error: "need_id_and_name" });
    const ck = `mf:claim:${id}`, lk = `mf:lead:${id}`;
    if (b.action === "claim") {
      const mine = JSON.stringify({ by: name, at: Date.now() });
      const [set, cur] = await redis([["SET", ck, mine, "NX"], ["GET", ck]]);
      const c = parse(cur);
      return res.json(set === "OK" || (c && c.by === name) ? { ok: true, claim: c } : { ok: false, claim: c });
    }
    if (b.action === "release") {
      const [cur] = await redis([["GET", ck]]);
      const c = parse(cur);
      if (c && c.by !== name) return res.json({ ok: false, claim: c });
      await redis([["DEL", ck]]);
      return res.json({ ok: true });
    }
    if (b.action === "update") {
      // claim on first edit; refuse if someone else holds the lead
      const mine = JSON.stringify({ by: name, at: Date.now() });
      const [, cur, old] = await redis([["SET", ck, mine, "NX"], ["GET", ck], ["GET", lk]]);
      const c = parse(cur);
      if (c && c.by !== name) return res.json({ ok: false, claim: c });
      const patch = {};
      for (const f of FIELDS) if (b.patch && typeof b.patch[f] === "string") patch[f] = b.patch[f].slice(0, 2000);
      if (patch.status && !STATUSES.has(patch.status)) delete patch.status;
      const lead = { ...(parse(old) || {}), ...patch, updatedBy: name, updatedAt: Date.now() };
      await redis([["SET", lk, JSON.stringify(lead)]]);
      return res.json({ ok: true, lead, claim: c });
    }
    return res.status(400).json({ error: "unknown_action" });
  } catch (e) {
    return res.status(500).json({ error: "storage_error", detail: String(e.message || e).slice(0, 200) });
  }
};
