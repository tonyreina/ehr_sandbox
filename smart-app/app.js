// Patient dashboard. Two modes share all the rendering code:
//   open   - the Oracle Health open sandbox (public, read-only, no login or registration)
//   signed - a SMART on FHIR session (launched from code Console, see launch.html)
const $ = id => document.getElementById(id);
const cfg = window.SMART_CONFIG;
let profile = null, profileKey = null;   // the active EHR profile, chosen in main()

function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;          // textContent only: server data is never HTML
  if (cls) e.className = cls;
  return e;
}

function simpleTable(headers, rows, numericCols = []) {
  const t = el("table");
  const hr = t.createTHead().insertRow();
  headers.forEach(h => hr.append(el("th", h)));
  const body = t.createTBody();
  for (const r of rows) {
    const tr = body.insertRow();
    r.forEach((cell, i) => {
      const td = tr.insertCell();
      if (cell instanceof Node) td.append(cell); else td.textContent = cell;
      if (numericCols.includes(i)) td.className = "num";
    });
  }
  const wrap = el("div", undefined, "table-wrap");   // scrolls sideways on narrow screens
  wrap.append(t);
  return wrap;
}

const badge = text => (text ? el("span", text, "badge") : "");

// ---- sections ---------------------------------------------------------------------------------

function renderTiles(charts) {
  const box = $("tiles"); box.replaceChildren();
  for (const c of charts) {
    const s = c.series.find(s => s.points.length);
    if (!s) continue;
    const tile = el("div", undefined, "tile");
    tile.append(el("div", c.title, "label"));
    const last = p => p && p.v;
    const value = c.series.length > 1
      ? c.series.map(s => { const p = s.points[s.points.length - 1]; return p ? Math.round(p.v) : "–"; }).join("/")
      : String(Math.round(last(s.points[s.points.length - 1]) * 10) / 10);
    const v = el("div", value, "value");
    v.append(el("span", c.unit, "unit"));
    tile.append(v, el("div", s.points[s.points.length - 1].date, "when"));
    box.append(tile);
  }
  if (!box.children.length) box.append(el("p", "No recent vital signs.", "muted"));
}

function renderCharts(charts) {
  const box = $("charts"); box.replaceChildren();
  let hidden = 0;
  for (const c of charts) {
    hidden += c.hiddenFuture;
    if (!c.series.some(s => s.points.length)) continue;
    const card = el("div", undefined, "chart-card");
    card.append(el("h3", c.title));
    const n = Math.max(...c.series.map(s => s.points.length));
    card.append(el("div", `${c.unit} · ${n} readings`, "sub"));
    if (c.series.length > 1) {                              // legend for 2+ series
      const lg = el("div", undefined, "legend");
      c.series.forEach((s, i) => {
        const item = el("span"); const key = el("span", undefined, "tip-key");
        key.style.background = `var(--series-${i + 1})`;
        item.append(key, document.createTextNode(s.name)); lg.append(item);
      });
      card.append(lg);
    }
    const plot = el("div", undefined, "plot");
    lineChart(c, plot);
    card.append(plot);
    const d = el("details"); d.append(el("summary", "Table view"), chartTable(c));
    card.append(d);
    box.append(card);
  }
  if (!box.children.length) box.append(el("p", "No vital-sign readings for this patient.", "muted"));
  $("future-note").hidden = !hidden;
  $("future-note").textContent = `${hidden} future-dated sandbox reading${hidden > 1 ? "s" : ""} hidden.`;
}

function renderLabs(observations) {
  const groups = groupLabs(observations);
  const box = $("labs"); box.replaceChildren();
  if (!groups.length) return box.append(el("p", "No numeric lab results.", "muted"));
  box.append(simpleTable(
    ["Test", "Latest", "Date", "Trend", "Results"],
    groups.slice(0, 12).map(g => [g.name, `${g.latest.v} ${g.unit}`, g.latest.date, sparkline(g.points), String(g.points.length)]),
    [1, 4]));
  if (groups.length > 12) box.append(el("p", `…and ${groups.length - 12} more tests.`, "muted"));
}

const MAX_ROWS = 10;
function renderList(id, rows, headers, empty, noun) {
  const box = $(id); box.replaceChildren();
  if (!rows.length) return box.append(el("p", empty, "muted"));
  box.append(simpleTable(headers, rows.slice(0, MAX_ROWS)));
  if (rows.length > MAX_ROWS) box.append(el("p", `…and ${rows.length - MAX_ROWS} more ${noun}.`, "muted"));
}

// ---- data loading -----------------------------------------------------------------------------

let current = 0;   // ignore responses that arrive after the user picked another patient

async function bundle(client, query, { timeout = 0 } = {}) {
  const req = client.request(query);
  const b = timeout
    ? await Promise.race([req, new Promise((_, rej) => setTimeout(() => rej(new Error(`timed out after ${timeout / 1000}s`)), timeout))])
    : await req;
  return (b.entry || []).map(e => e.resource);
}

// Fills a section independently so one slow or forbidden resource never blocks the page.
async function section(token, id, load, render) {
  const box = $(id);
  box.replaceChildren(el("p", "Loading… (the sandbox can take 10+ seconds)", "muted loading"));
  try {
    const data = await load();
    if (token === current) render(data);
  } catch (e) {
    if (token !== current) return;
    box.replaceChildren(el("p", /40[13]|insufficient/i.test(e.message)
      ? `Not authorized. Register this resource's scope with ${profile.name} and add it to profiles.${profileKey}.resources in smart-app/config.js.`
      : `Unavailable: ${e.message}`, "muted"));
  }
}

async function loadPatient(client, patientId) {
  const token = ++current;
  $("status").className = "muted";
  $("status").textContent = `Loading patient ${patientId}…`;
  const pid = encodeURIComponent(patientId);
  let p;
  try {
    p = await client.request(`Patient/${pid}`);
  } catch (e) {
    $("status").textContent = `Failed to load patient ${patientId}: ${e.message}`;
    $("status").className = "error";
    return;
  }
  if (token !== current) return;
  $("status").textContent = "";
  const age = ageFromBirthDate(p.birthDate);
  $("name").textContent = patientName(p);
  $("demographics").textContent = [p.gender, age !== null ? `${age} years` : null,
    p.birthDate ? `born ${p.birthDate}` : null, `ID ${p.id}`].filter(Boolean).join(" · ");
  $("dash").hidden = false;

  const obs = category => () => bundle(client, `Observation?patient=${pid}&category=${category}&_sort=-date&_count=100`);
  await Promise.all([
    section(token, "charts", obs("vital-signs"), data => {
      const charts = VITALS.map(spec => buildVitalChart(spec, data));
      renderTiles(charts); renderCharts(charts);
    }),
    section(token, "labs", obs("laboratory"), renderLabs),
    section(token, "meds", () => bundle(client, `MedicationRequest?patient=${pid}&_count=50`), rs =>
      renderList("meds", medications(rs).map(m => [m.name, m.dose, badge(m.status)]),
        ["Medication", "Dose", "Status"], "No medications on file.", "medications")),
    section(token, "allergies", () => bundle(client, `AllergyIntolerance?patient=${pid}&_count=50`), rs =>
      renderList("allergies", allergies(rs).map(a => [a.name, a.reactions, badge(a.criticality)]),
        ["Allergen", "Reactions", "Criticality"], "No known allergies on file.", "allergies")),
    section(token, "encounters", () => bundle(client, `Encounter?patient=${pid}&_count=20`), rs => {
      const es = encounters(rs);
      // The sandbox often has no encounter dates; show where instead of a column of dashes.
      const dated = es.some(e => e.date);
      renderList("encounters",
        es.map(e => [...(dated ? [e.date || "–"] : []), e.kind, e.where || "–", badge(e.status)]),
        [...(dated ? ["Date"] : []), "Type", "Location", "Status"], "No encounters on file.", "encounters");
    }),
    // The sandbox is slow for Condition searches on large test charts, so bound the wait.
    section(token, "conditions", () => bundle(client, `Condition?patient=${pid}${profile.conditionCategory ? `&category=${profile.conditionCategory}` : ""}`, { timeout: 45000 }), rs =>
      renderList("conditions", conditions(rs).map(c => [c.name, c.date || "–", badge(c.status)]),
        ["Problem", "Onset", "Status"], "No problems on file.", "problems")),
  ]);
}

// ---- picker -----------------------------------------------------------------------------------

function fillPicker(select, options, selected) {
  select.replaceChildren();
  for (const o of options) {
    const opt = el("option", `${o.label} (${o.id})`);
    opt.value = o.id;
    select.append(opt);
  }
  if (selected) select.value = selected;
}

// browse=false (a patient/* scope): only the launch patient is readable, so no list or search.
async function setupPicker(client, launchPatient, browse) {
  const select = $("patient-select");
  const base = [];
  if (launchPatient) base.push({ id: launchPatient, label: "Launch patient" });
  if (browse) for (const p of profile.patients || []) if (!base.some(o => o.id === p.id)) base.push(p);
  if (browse && !base.length) {              // e.g. HAPI: no fixed test patients, list what the server has
    try {
      const found = await bundle(client, "Patient?_count=20");
      for (const p of found) base.push({ id: p.id, label: `${patientName(p) || "(unnamed)"}${p.birthDate ? ", " + p.birthDate : ""}` });
    } catch (e) { $("status").textContent = `Could not list patients: ${e.message}`; $("status").className = "error"; }
  }
  fillPicker(select, base, base[0] && base[0].id);
  $("search").hidden = $("search-btn").hidden = !browse;

  select.addEventListener("change", () => loadPatient(client, select.value));
  $("picker").addEventListener("submit", async e => {
    e.preventDefault();
    const text = $("search").value.trim();
    if (!text) return;
    $("status").className = "muted";
    $("status").textContent = `Searching for “${text}”…`;
    try {
      const found = await bundle(client, `Patient?name=${encodeURIComponent(text)}&_count=20`);
      if (!found.length) { $("status").textContent = `No patients match “${text}”.`; return; }
      fillPicker(select, found.map(p => ({ id: p.id, label: `${patientName(p)}${p.birthDate ? ", " + p.birthDate : ""}` })));
      $("status").textContent = `${found.length} match${found.length > 1 ? "es" : ""}.`;
      loadPatient(client, select.value);
    } catch (err) {
      $("status").textContent = `Search failed: ${err.message}`;
      $("status").className = "error";
    }
  });
  $("picker").hidden = !base.length && !browse;
  return base.length ? base[0].id : null;
}

// ---- EHR bar and sign-in ----------------------------------------------------------------------

const store = {
  get(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { sessionStorage.setItem(k, v); } catch (e) { /* storage blocked */ } },
  del(k) { try { sessionStorage.removeItem(k); } catch (e) { /* storage blocked */ } },
};

function setupEhrBar() {
  const select = $("ehr-select");
  for (const [k, p] of Object.entries(cfg.profiles)) {
    const o = el("option", p.name); o.value = k; select.append(o);
  }
  select.value = profileKey;
  select.addEventListener("change", () => {
    store.del("smart_autologin");
    window.location.href = `index.html?ehr=${encodeURIComponent(select.value)}`;   // fresh page: drops any stale ?code=
  });
  $("signin").addEventListener("click", () => {
    store.del("smart_autologin");
    window.location.href = `launch.html?ehr=${encodeURIComponent(profileKey)}`;
  });
  // The app can start the login itself only where the profile has a standalone iss.
  $("signin").hidden = !profile.standaloneIss;
}

// ---- start-up ---------------------------------------------------------------------------------

async function start(client, mode, note) {
  const where = client.state.serverUrl;
  $("mode").textContent = mode === "signed"
    ? `Signed in to ${profile.name} via SMART on FHIR · ${where}`
    : `${profile.name} · open (read-only, no login) · ${where}${profile.signedInNote ? " · " + profile.signedInNote : ""}`;
  if (note) { $("notice").textContent = note; $("notice").hidden = false; }
  const scope = (client.state.tokenResponse || {}).scope;
  const first = await setupPicker(client, mode === "signed" ? client.patient.id : null,
                                  canBrowsePatients(mode === "signed", scope));
  if (first) loadPatient(client, first);
  else if (mode === "signed") { $("status").textContent = "Signed in, but the EHR gave no patient context."; $("status").className = "error"; }
}

// An EHR without an open endpoint (Epic): start the login ourselves, once. A failed or cancelled
// sign-in returns here with a notice, which stops the redirect loop.
function requireSignIn(note) {
  $("mode").textContent = `${profile.name} requires sign-in`;
  const clientId = clientIdFor(profileKey, cfg, window.SMART_LOCAL);
  if (note) { $("notice").textContent = note; $("notice").hidden = false; }
  if (!clientId) {
    $("status").textContent = `No ${profile.name} client id yet. Run: pixi run smart-setup --ehr ${profileKey}. ${profile.launchHint || ""}`;
    return;
  }
  if (profile.standaloneIss && !note && !store.get("smart_autologin")) {
    store.set("smart_autologin", "1");
    $("status").textContent = `Redirecting to ${profile.name} sign-in…`;
    window.location.replace(`launch.html?ehr=${encodeURIComponent(profileKey)}`);
    return;
  }
  $("status").textContent = profile.standaloneIss
    ? `Use Sign in to log in to ${profile.name}.`
    : (profile.launchHint || "Launch the app from the EHR.");
}

(async function main() {
  const q = new URLSearchParams(window.location.search);
  const returning = q.has("code") || q.has("error") || !!store.get("SMART_KEY");
  profileKey = chooseProfile(cfg, { ehrParam: q.get("ehr"), saved: returning ? store.get("smart_ehr") : null, def: window.SMART_DEFAULT_EHR });
  profile = cfg.profiles[profileKey];
  const openBase = q.get("base") || profile.openBase;    // ?base= points an open profile at another server
  setupEhrBar();

  let note = "";
  if (q.has("error")) {
    const uri = decodeURIComponent(q.get("error_uri") || "");
    const persona = (uri.match(/persona=([a-z]+)/) || [])[1];
    note = `Sign-in failed: ${q.get("error")} ${q.get("error_description") || ""}` +
      (persona ? ` [persona=${persona}]` : "") + (uri.includes("persona-mismatch")
        ? " — the app type doesn't match this launch (Provider apps launch from the EHR; Patient apps from Sign in)." : "") +
      (openBase ? " Showing the open sandbox instead." : "");
  } else if (q.has("code") || store.get("SMART_KEY")) {
    try {
      const client = await FHIR.oauth2.ready();
      store.del("smart_autologin");
      return start(client, "signed");
    } catch (e) {
      note = `SMART session unavailable (${e.message}).` + (openBase ? " Showing the open sandbox instead." : "");
    }
  }
  if (openBase) return start(FHIR.client({ serverUrl: openBase }), "open", note);
  requireSignIn(note);
})();
