// Pure FHIR helpers (no DOM, no network) so they can be unit-tested under node.

function patientName(p) {
  const n = (p.name || []).find(x => x.use === "official") || (p.name || [])[0] || {};
  return n.text || [...(n.given || []), n.family].filter(Boolean).join(" ");
}

function ageFromBirthDate(birthDate, now = new Date()) {
  const m = /^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$/.exec(birthDate || "");   // birth dates can be partial
  if (!m) return null;
  let age = now.getFullYear() - Number(m[1]);
  const month = Number(m[2] || 1), day = Number(m[3] || 1);
  if (now.getMonth() + 1 < month || (now.getMonth() + 1 === month && now.getDate() < day)) age -= 1;
  return age;
}

function loincCodes(resource) {
  return ((resource.code || {}).coding || [])
    .filter(c => (c.system || "").includes("loinc"))
    .map(c => c.code);
}

function codeText(resource) {
  const c = resource.code || {};
  return c.text || (c.coding || [])[0]?.display || "Unknown";
}

// Some EHRs (Epic) report units as raw UCUM codes; show the familiar form.
const UNIT_LABELS = { "mm[Hg]": "mmHg", "Cel": "°C", "degC": "°C", "[degF]": "°F", "[lb_av]": "lb", "[in_i]": "in" };

function quantity(q) {
  if (!q || typeof q.value !== "number") return null;
  const unit = q.unit || q.code || "";
  return { value: q.value, unit: UNIT_LABELS[unit] || unit };
}

// Vital-sign charts. A series picks values out of an Observation by LOINC code, either from the
// observation's own valueQuantity or from one of its components (blood pressure).
const VITALS = [
  { key: "bp", title: "Blood pressure", codes: ["85354-9"], series: [
      { name: "Systolic",  component: "8480-6" },
      { name: "Diastolic", component: "8462-4" } ] },
  { key: "pulse", title: "Pulse",            codes: ["69000-8", "68999-2", "8867-4"], series: [{ name: "Pulse" }] },
  { key: "temp",  title: "Temperature",      codes: ["8310-5"],                       series: [{ name: "Temperature" }] },
  { key: "spo2",  title: "Oxygen saturation", codes: ["2708-6", "59408-5"],           series: [{ name: "SpO₂" }] },
  { key: "resp",  title: "Respiratory rate", codes: ["9279-1"],                       series: [{ name: "Resp. rate" }] },
  { key: "wt",    title: "Weight",           codes: ["29463-7", "3141-9"],            series: [{ name: "Weight" }] },
];

function pointValue(obs, serie) {
  if (serie.component) {
    const c = (obs.component || []).find(c => loincCodes({ code: c.code }).includes(serie.component));
    return quantity(c && c.valueQuantity);
  }
  return quantity(obs.valueQuantity);
}

// -> { title, unit, series: [{ name, points: [{t, v, date}] }], hiddenFuture }
function buildVitalChart(spec, observations, now = Date.now()) {
  const mine = observations.filter(o => loincCodes(o).some(c => spec.codes.includes(c)));
  let hiddenFuture = 0, unit = "";
  const series = spec.series.map(s => ({ name: s.name, points: [] }));
  for (const o of mine) {
    const t = Date.parse(o.effectiveDateTime || "");
    if (Number.isNaN(t)) continue;
    if (t > now) { hiddenFuture++; continue; }           // the shared sandbox has some far-future timestamps
    spec.series.forEach((s, i) => {
      const q = pointValue(o, s);
      if (q) { unit = unit || q.unit; series[i].points.push({ t, v: q.value, date: o.effectiveDateTime.slice(0, 10) }); }
    });
  }
  for (const s of series) s.points.sort((a, b) => a.t - b.t);
  return { key: spec.key, title: spec.title, unit, series, hiddenFuture: Math.round(hiddenFuture / spec.series.length) };
}

// Abnormal flag for a result: the EHR's own interpretation when given, else the reference range.
function labFlag(o, value) {
  const code = ((o.interpretation || []).flatMap(i => i.coding || [])[0] || {}).code;
  if (code && code !== "N") return code;                     // H, L, HH, LL, A, ...
  const r = (o.referenceRange || [])[0] || {};
  if (r.high && typeof r.high.value === "number" && value > r.high.value) return "H";
  if (r.low && typeof r.low.value === "number" && value < r.low.value) return "L";
  return "";
}

function rangeText(o) {
  const r = (o.referenceRange || [])[0] || {};
  if (r.text) return r.text;
  const lo = r.low && r.low.value, hi = r.high && r.high.value;
  if (lo !== undefined && hi !== undefined) return `${lo}–${hi}`;
  if (hi !== undefined) return `≤ ${hi}`;
  if (lo !== undefined) return `≥ ${lo}`;
  return "";
}

// Latest numeric result per test, with its history, for the lab table.
function groupLabs(observations, now = Date.now()) {
  const groups = new Map();
  for (const o of observations) {
    const q = quantity(o.valueQuantity);
    const t = Date.parse(o.effectiveDateTime || "");
    if (!q || Number.isNaN(t) || t > now) continue;
    const key = loincCodes(o)[0] || codeText(o);
    if (!groups.has(key)) groups.set(key, { name: codeText(o), unit: q.unit, points: [] });
    groups.get(key).points.push({ t, v: q.value, date: o.effectiveDateTime.slice(0, 10),
                                  flag: labFlag(o, q.value), range: rangeText(o) });
  }
  return [...groups.values()]
    .map(g => { g.points.sort((a, b) => a.t - b.t); g.latest = g.points[g.points.length - 1]; return g; })
    .sort((a, b) => b.points.length - a.points.length || a.name.localeCompare(b.name));
}

// Some sandbox sigs arrive as "X X"; show X once.
function dedupeText(s) {
  const t = (s || "").trim(), half = Math.floor(t.length / 2);
  return t.length > 3 && t.slice(0, half).trim() === t.slice(half).trim() ? t.slice(0, half).trim() : t;
}

// Flowsheet: one row per vital, one column per day (newest first), last reading of each day.
function buildFlowsheet(charts, maxCols = 6) {
  const days = [...new Set(charts.flatMap(c => c.series.flatMap(s => s.points.map(p => p.date))))]
    .sort().reverse().slice(0, maxCols);
  const rows = charts.filter(c => c.series.some(s => s.points.length)).map(c => ({
    label: c.title, unit: c.unit,
    cells: days.map(d => {
      const vals = c.series.map(s => { const ps = s.points.filter(p => p.date === d); return ps.length ? ps[ps.length - 1].v : null; });
      if (vals.every(v => v === null)) return "";
      return vals.map(v => (v === null ? "–" : Number(v.toFixed(1)).toString())).join("/");
    }),
  }));
  return { days, rows: rows.filter(r => r.cells.some(Boolean)) };   // drop vitals not taken on these days
}

function initials(name) {
  const parts = (name || "").replace(/,/g, " ").split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  // "LAST, FIRST" (Cerner text) vs "First Last": prefer first-name initial first.
  const [first, last] = /,/.test(name || "") ? [parts[1] || "", parts[0]] : [parts[0], parts[parts.length - 1]];
  return ((first[0] || "") + (last && last !== first ? last[0] : "")).toUpperCase();
}

function medications(resources) {
  const seen = new Set();
  return resources.map(r => ({
    name: (r.medicationCodeableConcept || {}).text || (r.medicationReference || {}).display || "Medication",
    dose: dedupeText(((r.dosageInstruction || [])[0] || {}).text),
    status: r.status || "",
    date: (r.authoredOn || "").slice(0, 10),
  })).filter(m => { const k = m.name + "|" + m.dose + "|" + m.status; return seen.has(k) ? false : seen.add(k); })
     .sort((a, b) => (a.status === "active" ? 0 : 1) - (b.status === "active" ? 0 : 1) || b.date.localeCompare(a.date));
}

function allergies(resources) {
  const seen = new Map();
  for (const r of resources) {
    const name = codeText(r);
    if (seen.has(name)) continue;
    seen.set(name, {
      name,
      status: ((r.clinicalStatus || {}).coding || [])[0]?.code || "",
      criticality: r.criticality || "",
      reactions: [...new Set((r.reaction || []).flatMap(x => (x.manifestation || []).map(m => m.text)).filter(Boolean)
      .flatMap(t => t.split(",")).map(t => t.trim()).filter(Boolean))].join(", "),
    });
  }
  return [...seen.values()];
}

function encounters(resources) {
  return resources.map(r => ({
    date: ((r.period || {}).start || "").slice(0, 10),
    kind: (r.type || []).map(t => t.text).filter(Boolean).join(", ") || "Encounter",
    cls: (r.class || {}).code || "",
    where: (((r.location || [])[0] || {}).location || {}).display || (r.serviceProvider || {}).display || "",
    status: r.status || "",
  })).sort((a, b) => b.date.localeCompare(a.date));
}

function conditions(resources) {
  const seen = new Map();
  for (const r of resources) {
    const name = codeText(r);
    if (seen.has(name)) continue;
    seen.set(name, {
      name,
      status: ((r.clinicalStatus || {}).coding || [])[0]?.code || "",
      date: (r.onsetDateTime || r.recordedDate || "").slice(0, 10),
    });
  }
  return [...seen.values()];
}

// ---- EHR profiles (see config.js) -------------------------------------------------------------

// Which profile applies: the iss host of a launch wins, then ?ehr=, the profile saved when the
// sign-in started, the CLI's default, and finally config.ehr.
function chooseProfile(cfg, { iss, ehrParam, saved, def } = {}) {
  const keys = Object.keys(cfg.profiles);
  if (iss) {
    try {
      const host = new URL(iss).hostname;
      const hit = keys.find(k => cfg.profiles[k].issMatch && host.includes(cfg.profiles[k].issMatch));
      if (hit) return hit;
    } catch (e) { /* not a URL: fall through */ }
  }
  for (const k of [ehrParam, saved, def, cfg.ehr]) if (k && cfg.profiles[k]) return k;
  return keys[0];
}

// Client ids live in config.local.js ({clientIds: {cerner: "...", epic: "..."}}); the older
// single `clientId` setting still maps to Cerner.
function clientIdFor(key, cfg, local) {
  return ((local || {}).clientIds || {})[key] || (key === "cerner" ? cfg.clientId : "") || "";
}

// EHR launch (the EHR opens the app, `launch` scope) vs standalone (the app starts the login).
function scopesFor(profile, { ehrLaunch, prefixOverride } = {}) {
  const prefix = prefixOverride || (ehrLaunch ? profile.ehrScopePrefix : profile.standaloneScopePrefix);
  return [ehrLaunch ? "launch" : "launch/patient", ...profile.extraScopes,
          ...profile.resources.map(r => `${prefix}/${r}.read`)].join(" ");
}

// user/* scopes can read any patient the user may see; patient/* scopes only the launch patient.
function canBrowsePatients(signedIn, scopeString) {
  return !signedIn || /(^|\s)user\//.test(scopeString || "");
}

// Exactly what the AI receives, in two parts: the system message, then the user message built from the template.
function promptParts(prompt, chart, question) {
  const user = prompt.template.replace(/\{(chart|question)\}/g, (_, k) => (k === "chart" ? chart : question));
  return {
    system: `SYSTEM MESSAGE (standing instructions)\n${prompt.instructions.trim()}`,
    user: `USER MESSAGE (chart and your question)\n${user}`,
  };
}

function promptText(prompt, chart, question) {
  const p = promptParts(prompt, chart, question);
  return `${p.system}\n\n${p.user}`;
}

if (typeof module !== "undefined") {
  module.exports = { promptParts, promptText, labFlag, rangeText, buildFlowsheet, initials, chooseProfile, clientIdFor, scopesFor, canBrowsePatients, patientName, ageFromBirthDate, VITALS, buildVitalChart, groupLabs, medications, allergies, encounters, conditions };
}
