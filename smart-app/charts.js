// Dependency-free SVG line charts. Colors come from CSS custom properties (see style.css).
const SVGNS = "http://www.w3.org/2000/svg";

function svg(tag, attrs = {}, text) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text !== undefined) e.textContent = text;
  return e;
}

function niceTicks(min, max, n = 3) {
  if (min === max) { min -= 1; max += 1; }
  const raw = (max - min) / n;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw);
  const lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step;
  const ticks = [];
  for (let v = lo; v <= hi + step / 2; v += step) ticks.push(Number(v.toFixed(6)));
  return ticks;
}

const fmt = v => (Math.abs(v) >= 100 ? v.toFixed(0) : Number(v.toFixed(2)).toString());
const fmtDate = t => new Date(t).toISOString().slice(0, 10);

// chart = { title, unit, series: [{ name, points: [{t, v}] }] }; series i uses var(--series-{i+1}).
function lineChart(chart, container) {
  const W = 420, H = 170, M = { t: 10, r: chart.series.length > 1 ? 70 : 16, b: 24, l: 40 };
  const all = chart.series.flatMap(s => s.points);
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart", role: "img", tabindex: "0",
    "aria-label": `${chart.title} over time` });
  if (!all.length) return null;

  const t0 = Math.min(...all.map(p => p.t)), t1 = Math.max(...all.map(p => p.t));
  const ticks = niceTicks(Math.min(...all.map(p => p.v)), Math.max(...all.map(p => p.v)));
  const y0 = ticks[0], y1 = ticks[ticks.length - 1];
  const x = t => M.l + (t1 === t0 ? (W - M.l - M.r) / 2 : ((t - t0) / (t1 - t0)) * (W - M.l - M.r));
  const y = v => M.t + (1 - (v - y0) / (y1 - y0)) * (H - M.t - M.b);

  for (const tk of ticks) {                                   // hairline grid + y labels
    root.append(svg("line", { x1: M.l, x2: W - M.r, y1: y(tk), y2: y(tk), class: "gl" }));
    root.append(svg("text", { x: M.l - 6, y: y(tk) + 4, class: "tick", "text-anchor": "end" }, fmt(tk)));
  }
  root.append(svg("text", { x: M.l, y: H - 6, class: "tick" }, fmtDate(t0)));
  if (t1 !== t0) root.append(svg("text", { x: W - M.r, y: H - 6, class: "tick", "text-anchor": "end" }, fmtDate(t1)));

  chart.series.forEach((s, i) => {
    if (!s.points.length) return;
    const color = `var(--series-${i + 1})`;
    if (s.points.length > 1) {
      root.append(svg("polyline", { points: s.points.map(p => `${x(p.t)},${y(p.v)}`).join(" "),
        class: "line", style: `stroke:${color}` }));
    }
    const last = s.points[s.points.length - 1];                // end dot with a surface ring
    root.append(svg("circle", { cx: x(last.t), cy: y(last.v), r: 4, class: "dot", style: `fill:${color}` }));
    if (chart.series.length > 1) {                              // direct label at the line end
      root.append(svg("text", { x: x(last.t) + 9, y: y(last.v) + 4, class: "endlabel" }, s.name));
    }
  });

  const cross = svg("line", { y1: M.t, y2: H - M.b, class: "cross", visibility: "hidden" });
  root.append(cross);
  const tip = document.createElement("div");
  tip.className = "tip"; tip.hidden = true;
  container.append(root, tip);

  // Crosshair snaps to the nearest observation date across all series.
  const times = [...new Set(all.map(p => p.t))].sort((a, b) => a - b);
  let idx = times.length - 1;
  function show(i) {
    idx = Math.max(0, Math.min(times.length - 1, i));
    const t = times[idx], px = x(t);
    cross.setAttribute("x1", px); cross.setAttribute("x2", px); cross.setAttribute("visibility", "visible");
    tip.replaceChildren();
    const head = document.createElement("div"); head.className = "tip-date"; head.textContent = fmtDate(t);
    tip.append(head);
    chart.series.forEach((s, k) => {
      const p = s.points.find(p => p.t === t);
      if (!p) return;
      const row = document.createElement("div"); row.className = "tip-row";
      const key = document.createElement("span"); key.className = "tip-key"; key.style.background = `var(--series-${k + 1})`;
      const val = document.createElement("strong"); val.textContent = `${fmt(p.v)} ${chart.unit}`;
      const name = document.createElement("span"); name.className = "tip-name"; name.textContent = s.name;
      row.append(key, val, name); tip.append(row);
    });
    tip.hidden = false;
    const box = root.getBoundingClientRect();
    const left = (px / W) * box.width;
    tip.style.left = `${Math.min(Math.max(left, 60), box.width - 60)}px`;
  }
  const hide = () => { cross.setAttribute("visibility", "hidden"); tip.hidden = true; };

  root.addEventListener("pointermove", e => {
    const box = root.getBoundingClientRect();
    const px = ((e.clientX - box.left) / box.width) * W;
    let best = 0;
    times.forEach((t, i) => { if (Math.abs(x(t) - px) < Math.abs(x(times[best]) - px)) best = i; });
    show(best);
  });
  root.addEventListener("pointerleave", hide);
  root.addEventListener("keydown", e => {
    if (e.key === "ArrowLeft") { show(idx - 1); e.preventDefault(); }
    if (e.key === "ArrowRight") { show(idx + 1); e.preventDefault(); }
    if (e.key === "Escape") hide();
  });
  root.addEventListener("focus", () => show(idx));
  root.addEventListener("blur", hide);
  return root;
}

// Tiny trend line for tables: muted line, accent end dot. Decorative; values are in the cells.
function sparkline(points, w = 90, h = 24) {
  const root = svg("svg", { viewBox: `0 0 ${w} ${h}`, class: "spark", "aria-hidden": "true" });
  if (points.length < 2) return root;
  const t0 = points[0].t, t1 = points[points.length - 1].t;
  const lo = Math.min(...points.map(p => p.v)), hi = Math.max(...points.map(p => p.v));
  const x = t => 4 + ((t - t0) / (t1 - t0 || 1)) * (w - 8);
  const y = v => 4 + (1 - (v - lo) / (hi - lo || 1)) * (h - 8);
  root.append(svg("polyline", { points: points.map(p => `${x(p.t)},${y(p.v)}`).join(" "), class: "spark-line" }));
  const last = points[points.length - 1];
  root.append(svg("circle", { cx: x(last.t), cy: y(last.v), r: 3, class: "spark-dot" }));
  return root;
}

// The always-available table view for a chart (tooltips never gate the data).
function chartTable(chart) {
  const table = document.createElement("table");
  const head = table.createTHead().insertRow();
  for (const h of ["Date", ...chart.series.map(s => `${s.name} (${chart.unit})`)]) {
    const th = document.createElement("th"); th.textContent = h; head.append(th);
  }
  const times = [...new Set(chart.series.flatMap(s => s.points.map(p => p.t)))].sort((a, b) => b - a);
  const body = table.createTBody();
  for (const t of times) {
    const tr = body.insertRow();
    tr.insertCell().textContent = fmtDate(t);
    for (const s of chart.series) {
      const p = s.points.find(p => p.t === t);
      tr.insertCell().textContent = p ? fmt(p.v) : "";
    }
  }
  return table;
}
