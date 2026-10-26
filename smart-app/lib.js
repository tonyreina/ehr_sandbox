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

function quantity(q) {
  return q && typeof q.value === "number" ? { value: q.value, unit: q.unit || "" } : null;
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

// Latest numeric result per test, with its history, for the lab table.
function groupLabs(observations, now = Date.now()) {
  const groups = new Map();
  for (const o of observations) {
    const q = quantity(o.valueQuantity);
    const t = Date.parse(o.effectiveDateTime || "");
    if (!q || Number.isNaN(t) || t > now) continue;
    const key = loincCodes(o)[0] || codeText(o);
    if (!groups.has(key)) groups.set(key, { name: codeText(o), unit: q.unit, points: [] });
    groups.get(key).points.push({ t, v: q.value, date: o.effectiveDateTime.slice(0, 10) });
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

if (typeof module !== "undefined") {
  module.exports = { patientName, ageFromBirthDate, VITALS, buildVitalChart, groupLabs, medications, allergies, encounters, conditions };
}
