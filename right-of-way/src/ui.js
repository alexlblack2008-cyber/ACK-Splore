"use strict";
// ─── Right-of-Way · panels, input and the main loop ─────────────────────────

const $ = id => document.getElementById(id);
const money = v => (v < 0 ? "−$" : "$") + Math.abs(Math.round(v)).toLocaleString();
let tool = "inspect", speed = 1;

// ── toolbox ──────────────────────────────────────────────────────────────────
function buildTools() {
  const groups = {}; TOOLS.forEach(t => (groups[t.group] ||= []).push(t));
  $("tools").innerHTML = Object.entries(groups).map(([g, ts]) => `<div class="tgroup"><span>${g}</span><div class="list">${ts.map(t => {
    const locked = !unlocked(t.id);
    const price = t.cost ? "$" + (t.cost >= 1000 ? (t.cost / 1000) + "k" : t.cost) : "";
    return `<button class="tool" data-tool="${t.id}" aria-pressed="${tool === t.id || (tool === "place" && placing && placing.type === t.id)}" ${locked ? "disabled" : ""} title="${t.name}${t.key ? " (" + t.key.toUpperCase() + ")" : ""}${locked ? " · unlocks at " + t.unlock.toLocaleString() + " residents" : ""}">
      <span class="sw" style="background:${t.sw}">${t.glyph || ""}</span><span class="nm">${t.name}</span><span class="cs">${locked ? "🔒 " + (t.unlock >= 1000 ? t.unlock / 1000 + "k" : t.unlock) : price}${t.key ? ` <kbd>${t.key.toUpperCase()}</kbd>` : ""}</span></button>`;
  }).join("")}</div></div>`).join("");
  $("toolDesc").textContent = tool === "place" && placing ? placeHint() : TOOL[tool].desc;
  if (S.tut.on) focusPulse();
}
function focusPulse() { const st = tutStep(); document.querySelectorAll(".tool.pulse").forEach(b => b.classList.remove("pulse")); if (st && st.tool) { const b = document.querySelector(`.tool[data-tool="${st.tool}"]`); if (b) b.classList.add("pulse"); } }
function placeHint() { return `Placing the ${LABEL[placing.type]} by ${ARCH_BY[placing.arch].firm}. Click a site on the map. Press O to rotate, Esc to cancel.`; }
function setTool(id) {
  if (id !== "place") placing = null;
  tool = id;
  document.querySelectorAll(".tool").forEach(b => b.setAttribute("aria-pressed", b.dataset.tool === id || (id === "place" && placing && b.dataset.tool === placing.type)));
  $("toolDesc").textContent = id === "place" && placing ? placeHint() : TOOL[id].desc;
  $("placeBar").hidden = id !== "place";
  if (id === "place") $("placeText").textContent = placeHint();
  cv.style.cursor = id === "inspect" ? "grab" : "crosshair";
}

// ── overlays ─────────────────────────────────────────────────────────────────
const OVERLAYS = [["base", "Plan"], ["cond", "Condition"], ["traffic", "Traffic LOS"], ["value", "Land value"], ["power", "Power"], ["water", "Water"], ["sewer", "Sewer"]];
const LEGENDS = {
  base: [["#EFD77A", "Residential"], ["#E39A96", "Commercial"], ["#B4A2D6", "Industrial"], ["#E8590C", "Work order"]],
  cond: [["#2F7D4F", "Good"], ["#D69A12", "Fair"], ["#BF3A2B", "Failing"]],
  traffic: [["#2F7D4F", "LOS A"], ["#A8A523", "C"], ["#D69A12", "D"], ["#D5661C", "E"], ["#BF3A2B", "F"]],
  value: [["#2F7D4F", "High"], ["#D69A12", "Average"], ["#BF3A2B", "Low"], ["rgba(191,58,43,.3)", "Runway zone"]],
  power: [["#3F7CAC", "Served"], ["#BF3A2B", "No service"], ["#E8590C", "Fault"], ["#9AA0A6", "Not connected"]],
};
LEGENDS.water = LEGENDS.power; LEGENDS.sewer = LEGENDS.power;
function buildOverlays() {
  $("overlays").innerHTML = `<span>Map layer</span>` + OVERLAYS.map(([k, n]) => `<button class="chip" data-ov="${k}" aria-pressed="${overlay === k}">${n}</button>`).join("")
    + `<div class="legend">${LEGENDS[overlay].map(([c, n]) => `<span><i style="background:${c}"></i>${n}</span>`).join("")}</div>`;
}

// ── panels ───────────────────────────────────────────────────────────────────
function renderNews() { const el = $("news"); if (!el || !S) return; el.innerHTML = S.news.slice(0, 40).map(n => `<div><time>${dateStr(n.d).replace(/, \d+$/, "")}</time><span class="${n.cls}">${n.text}</span></div>`).join(""); }
const tag = (ok, label) => `<span class="tag ${ok ? "ok" : "no"}">${label} ${ok ? "✓" : "✕"}</span>`;
function renderInspector() {
  const el = $("insp");
  if (!sel) { el.innerHTML = `<p class="muted">Pick <b>Inspect</b> and click any tile to see its condition, traffic and utility service.</p>`; $("inspXY").textContent = ""; return; }
  const { x, y } = sel, t = T_(x, y); $("inspXY").textContent = `grid ${street(x, y)}`;
  let h = "";
  const inc = S.inc.find(i => i.status !== "done" && i.x === x && i.y === y);
  if (isRoad(t)) {
    const vc = vcOf(t);
    const name = `${ROAD[t.b].name}${t.st === "bridge" ? " bridge" : t.st === "tunnel" ? " tunnel" : ""}${t.ix ? " · intersection" : ""}`;
    h += `<h3>${name}</h3><dl class="kv">`;
    h += t.st === "bridge" ? `<dt>NBI superstructure rating</dt><dd>${nbi(t.cond)} of 9${nbi(t.cond) <= 4 ? " · deficient" : ""}</dd>` : `<dt>${t.st === "tunnel" ? "Liner condition" : "Pavement condition (PCI)"}</dt><dd>${t.cond.toFixed(0)} · ${pciLabel(t.cond)}</dd>`;
    h += `<dt>Peak volume / capacity</dt><dd>${t.load.toFixed(0)} / ${effCap(t).toFixed(0)} veh/h</dd><dt>V/C ratio</dt><dd>${vc.toFixed(2)}</dd><dt>Level of service</dt><dd>${los(vc)}</dd>`;
    if (t.ix) h += `<dt>Control</dt><dd>${t.ctl === "signal" ? "Signalized" : t.ctl === "round" ? "Roundabout" : "Stop signs"}</dd>`;
    h += `</dl><p>${tag(!t.fP && t.r_power > 0, "Power")}${tag(!t.fW && t.r_water > 0, "Water main")}${tag(t.r_sewer > 0, "Sewer")}</p>`;
    if (!inc && t.cond < 99) h += `<div class="row"><button class="btn" data-repair="${x},${y}">Repair for ${money((100 - t.cond) * (t.st === "bridge" ? 25 : 6))}</button></div>`;
    if (vc >= 0.9 && t.b === "road") h += `<p class="muted">Near capacity. Widen to an avenue, add a parallel route, or control the intersection.</p>`;
    if (t.ix && !t.ctl && vc > 0.6) h += `<p class="muted">An uncontrolled intersection runs at 60% capacity. A signal or roundabout would help.</p>`;
  } else if (isZone(t)) {
    const lv = ["Vacant lot", "Low density", "Medium density", "High density"][t.lvl];
    h += `<h3>${ZONE[t.b].name} · ${lv}</h3><dl class="kv"><dt>${t.b === "R" ? "Residents" : "Jobs"}</dt><dd>${t.b === "R" ? ZONE.R.pop[t.lvl] : ZONE[t.b].jobs[t.lvl]}</dd>
      <dt>Land value</dt><dd>${Math.round(t.val * 100)}% of average</dd><dt>Power draw</dt><dd>${demandOf(t, "power").toFixed(2)} MW</dd><dt>Water use</dt><dd>${Math.round(demandOf(t, "water") * 1e6).toLocaleString()} gpd</dd></dl>`;
    h += `<p>${tag(accessTile(x, y) >= 0, "Street")}${tag(t.pw, "Power")}${tag(t.wt, "Water")}${tag(t.sw, "Sewer")}${tag(inRadius(x, y, "fire", RADIUS.fire), "Fire cover")}</p>`;
    if (accessTile(x, y) < 0) h += `<p class="muted">Needs a local street on one side. Highways don't count.</p>`;
    else if (!t.pw || !t.wt) h += `<p class="muted">Missing utilities. Check the Power and Water layers for breaks, or plants running over capacity.</p>`;
    else if (t.lvl === 2 && !t.sw) h += `<p class="muted">Needs sewer service to grow past medium density.</p>`;
    if (t.rpz) h += `<p class="muted">Inside a runway protection zone: capped at low density.</p>`;
  } else if (t.b === "proj") {
    const p = proj(t.pid), d = PROJ[p.type], a = ARCH_BY[p.arch];
    h += `<h3>${p.name}</h3><dl class="kv"><dt>Architect</dt><dd>${a.firm}</dd>${p.golf ? `<dt>Course</dt><dd>${GOLF_BY[p.golf].firm}</dd>` : ""}
      <dt>Status</dt><dd>${p.status === "build" ? `Under construction · ${Math.round(p.prog / p.days * 100)}%` : "Open"}</dd><dt>Jobs</dt><dd>${d.jobs}</dd><dt>Upkeep</dt><dd>${money(d.upkeep * a.upkeep)}/mo</dd>
      ${p.golf ? `<dt>Irrigation now</dt><dd>${projDemand(p, "water").toFixed(3)} MGD</dd>` : ""}</dl>`;
    if (p.status === "open") h += `<p>${tag(p.pw, "Power")}${tag(p.wt, "Water")}${tag(p.sw, "Sewer")}${d.rpz ? tag(p.landside !== false, "Highway ramp within 10") : ""}</p>`;
    if (d.rpz && p.landside === false) h += `<p class="muted">No highway ramp nearby, so passenger numbers are down 40%.</p>`;
  } else if (t.b) {
    const tl = TOOL[t.b];
    h += `<h3>${tl.name}</h3><dl class="kv"><dt>Status</dt><dd>${t.off ? "Offline" : t.salt ? "Salt water intake" : t.link === false ? "Not on a street" : "Operating"}</dd><dt>Upkeep</dt><dd>${money(UPKEEP[t.b] || 0)}/mo</dd>`;
    if (CAP[t.b]) { const m = { power: "power", pump: "water", sewage: "sewer" }[t.b], n = S.net[m], u = t.b === "power" ? "MW" : "MGD";
      h += `<dt>Rated capacity</dt><dd>${CAP[t.b]} ${u}</dd><dt>Systemwide load</dt><dd>${n.supply ? Math.round(n.demand / n.supply * 100) + "%" : "n/a"}</dd>`; }
    h += `</dl><p class="muted">${tl.desc}</p>`;
  } else {
    const notes = { [SEA]: "Salt water. Bridges and tunnels can cross it; sewage plants can sit on its shore.", [FRESH]: "Fresh water. Water plants need to touch it.", [FOREST]: "Clearing adds $30 to anything built here.",
      [HILL]: "Cut and fill doubles construction costs. Good views raise land value.", [MARSH]: "Must be filled first: +$120 a tile. Floods easily.", [BEACH]: "Ocean frontage. A links golf course needs it.", [GRASS]: "Undeveloped parcel." };
    h += `<h3>${TER_NAME[t.ter]}</h3><dl class="kv"><dt>Land value</dt><dd>${Math.round(t.val * 100)}%</dd></dl><p class="muted">${notes[t.ter]}</p>`;
    if (t.rpz) h += `<p class="muted">Inside a runway protection zone.</p>`;
  }
  if (inc) { const d = INC[inc.kind]; h += `<p class="alert"><b>${d.name}.</b> ${d.desc}</p>`; }
  el.innerHTML = h;
}
function renderWO() {
  const open = S.inc.filter(i => i.status !== "done").sort((a, b) => (a.status !== "open") - (b.status !== "open") || INC[b.kind].sev - INC[a.kind].sev || a.start - b.start);
  const c = crews();
  $("woCount").textContent = `${open.filter(i => i.status === "open").length} open · crews ${c.free}/${c.total}`;
  $("wo").innerHTML = open.length ? open.slice(0, 12).map(i => { const d = INC[i.kind], age = S.day - i.start;
    const act = i.status === "crew" ? `<span class="status-pill">On site · ${i.left}d</span>` : i.status === "auto" ? `<span class="status-pill">Police on scene</span>`
      : `<button class="btn hv" data-dispatch="${i.id}" ${(i.kind !== "fire" && c.free <= 0) || S.funds < d.cost ? "disabled" : ""}>${i.kind === "fire" ? "Mutual aid" : "Dispatch"} ${money(d.cost)}</button>`;
    return `<div class="wo-item" data-goto="${i.x},${i.y}"><span class="sev s${d.sev}"></span><div><b>${d.name}</b><small>${street(i.x, i.y)} · open ${age}d${i.kind === "bridge" ? " · NBI " + nbi(T_(i.x, i.y).cond) : ""}</small></div>${act}</div>`; }).join("")
    : `<div class="empty">No open work orders. Use the quiet time to repair roads before they fail.</div>`;
}
function renderGrades() {
  let sum = 0, n = 0;
  $("grades").innerHTML = S.grades.map(([name, detail, score]) => { const L = letter(score); if (score != null) { sum += clamp(score, 0, 100); n++; }
    return `<div><span>${name}</span><small>${detail}</small></div><div class="g ${L}">${L === "NA" ? "n/a" : L}</div>`; }).join("");
  $("gpa").textContent = n ? `overall ${letter(sum / n)}` : "";
}
function renderRCI() {
  $("rci").innerHTML = [["R", COL.Rb], ["C", COL.Cb], ["I", COL.Ib]].map(([k, c]) => { const v = S.demand[k], h = Math.abs(v) * 50;
    return `<div class="bar"><div class="track"><div class="fill" style="background:${c};${v >= 0 ? `bottom:50%;height:${h}%` : `top:50%;height:${h}%;opacity:.45`}"></div></div><span>${k}</span></div>`; }).join("");
}
function renderBudget() {
  const m = S.month;
  $("budgetMonth").textContent = m ? m.label : "estimate";
  let rows, net;
  if (m) {
    rows = [["Property & business tax", m.tax], ["Water & sewer fees", m.fees], ["Airport & tourism", m.tour], ["Country club leases", m.club], ["Road upkeep", -m.road], ["Facilities & landmarks", -m.fac],
      ["Preventive maintenance", -m.maint], ["Emergency repairs", -m.emergency], ["Snow & ice", -m.snow], ["Water lost to breaks", -m.water], ["Fines & settlements", -m.fine], ["Debt service", -m.debt]].filter(r => r[1]);
    net = m.net;
  } else {
    const r = revenue(), pi = projectIncome(), ru = roadUpkeep(), fu = facilityUpkeep();
    rows = [["Est. tax", r.tax], ["Est. water & sewer fees", r.fees], ["Est. road upkeep", -ru], ["Est. facilities", -fu]];
    net = r.tax + r.fees + pi.tour + pi.club - ru - fu;
  }
  $("budget").innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${money(v)}</dd>`).join("") + `<dt class="tot">Net</dt><dd class="tot" style="color:${net < 0 ? "var(--bad)" : "var(--good)"}">${money(net)}</dd>`;
  $("tax").value = S.tax; $("taxv").textContent = S.tax + "%";
  $("snowBudget").checked = !!S.snowBudget;
  const active = S.bonds.length; $("bondBtn").disabled = active >= 4;
  $("bondInfo").textContent = active ? `${active} outstanding · $${active * 150}/mo` : "Repaid at $150/mo over 8 years";
}
function renderSaveStatus() {
  const el = $("saveState"); if (!el) return;
  if (saveStatus.error) { el.textContent = saveStatus.error; el.className = "save-state bad"; return; }
  if (!saveStatus.at) { el.textContent = cloud ? "Autosave on · account" : "Autosave on · this browser"; el.className = "save-state"; return; }
  const ago = Math.round((Date.now() - saveStatus.at) / 60000);
  el.textContent = `Saved ${ago < 1 ? "just now" : ago + " min ago"}${saveStatus.cloud ? " · account" : cloud ? " · browser" : ""}`; el.className = "save-state";
}
function updateUI() {
  $("sDate").textContent = dateStr(S.day);
  $("sFunds").textContent = money(S.funds); $("sFunds").classList.toggle("neg", S.funds < 0);
  $("sPop").textContent = S.pop.toLocaleString(); $("sJobs").textContent = S.jobs.toLocaleString();
  $("sHappy").textContent = Math.round(S.happy) + "%";
  $("sCommute").textContent = S.commute ? S.commute.toFixed(0) + " min" : "—";
  const conds = [];
  if (S.heat > 0) conds.push("Heat advisory"); if (S.snow > 0) conds.push(S.plowed ? "Snow, plowing" : "Snow emergency"); if (grace()) conds.push(`Calm first year · ${360 - S.day} days left`);
  $("titleblock").innerHTML = `<b>${REGION} · ${CITY} master plan</b><br>1 tile ≈ 1 block · ${S.net.power.demand.toFixed(0)}/${S.net.power.supply.toFixed(0)} MW · ${S.net.water.demand.toFixed(2)}/${S.net.water.supply.toFixed(2)} MGD${conds.length ? "<br>" + conds.join(" · ") : ""}`;
  renderWO(); renderGrades(); renderRCI(); renderBudget(); renderSaveStatus();
  if (sel) renderInspector();
  document.querySelectorAll(".speed button").forEach(b => b.setAttribute("aria-pressed", +b.dataset.sp === speed));
  checkTutorial();
}

// ── modals ───────────────────────────────────────────────────────────────────
function modal(html, wide) { $("modalCard").innerHTML = html; $("modalCard").classList.toggle("wide", !!wide); $("modal").hidden = false; }
function closeModal() { $("modal").hidden = true; }
function showHelp() {
  modal(`<h3>Commissioner's handbook</h3>
  <ul>
    <li><b>Streets are the right-of-way.</b> Power lines and water and sewer mains run under them. A plant only serves buildings on the street network it touches.</li>
    <li><b>Water plants need fresh water</b> (the Quill, the Iron, or Quarry Reservoir). Sewage plants can sit on any shore.</li>
    <li><b>Everything wears out.</b> Traffic and freeze-thaw wear pavement. Old streets break mains and open sinkholes. Bridges below NBI 3 close, and ignored ones collapse.</li>
    <li><b>Traffic is routed.</b> Commuters pick the fastest path to jobs, and congestion slows a route (the BPR curve), so a new highway or avenue pulls traffic off side streets. Highways connect only through ramps. Uncontrolled four-way crossings lose 40% of their capacity.</li>
    <li><b>Landmarks go out to bid.</b> City Hall, airports and country clubs each get proposals from competing architects with different costs, build times, upkeep, public reaction and visitor appeal.</li>
    <li><b>Weather follows the calendar:</b> nor'easters in winter, pothole season Feb–Apr, spring river floods, summer heat, hurricanes in the fall. Levees protect the shore.</li>
    <li><b>Saving:</b> the game autosaves every month and whenever you leave the page. Use Save for manual slots, or export a save file to move between devices.</li>
  </ul>
  <p class="muted">Keys: 1–9, 0 tools · Q inspect · H highway · J ramp · T tunnel · G signal · K roundabout · E repair · X demolish · O rotate · arrows or WASD pan · +/− zoom · Space pause</p>
  <div class="row"><button class="btn hv" data-close>Back to work</button></div>`);
}
async function showSaves() {
  modal(`<h3>Save & load</h3><p class="muted">${cloud ? "Saves go to this browser and to your claude.ai account, so they follow you to other devices." : "Saves go to this browser. Export a save file to keep a backup or move to another device."} The game also autosaves every month and when you leave.</p>
    <div class="slots" id="slots"><p class="muted">Reading saves…</p></div>
    <div class="row"><button class="btn" id="exportBtn">Export save file</button><label class="btn" for="importFile">Load from file</label><input type="file" id="importFile" accept=".json,application/json" hidden><button class="btn ghost" id="pasteBtn">Paste save code</button></div>
    <textarea id="saveCode" hidden rows="3" placeholder="Paste a save code here" aria-label="Save code"></textarea>
    <div class="row"><button class="btn" data-close>Close</button></div>`);
  $("exportBtn").onclick = exportSave;
  $("importFile").onchange = e => { const f = e.target.files[0]; if (!f) return; f.text().then(txt => { if (importSave(txt)) closeModal(); }); };
  $("pasteBtn").onclick = () => { const ta = $("saveCode"); ta.hidden = false; ta.value = ""; ta.focus(); ta.oninput = () => { if (ta.value.trim().startsWith("{") && ta.value.trim().endsWith("}")) { if (importSave(ta.value.trim())) closeModal(); } }; };
  const info = await slotInfo();
  $("slots").innerHTML = info.map(s => `<div class="slot"><div><b>${s.name}</b><small>${saveLabel(s.sv)}</small></div>
    ${s.id !== "auto" ? `<button class="btn" data-save="${s.id}">Save here</button>` : ""}<button class="btn hv" data-load="${s.id}" ${s.sv ? "" : "disabled"}>Load</button></div>`).join("");
}
async function showWelcome() {
  const sv = await newestSave("auto");
  modal(`<p class="eyebrow">${REGION}</p><h3 class="big">Right-of-Way</h3>
    <p>You're the new Commissioner of Public Works for <b>${CITY}</b>, a harbor town on its way to becoming a city. Build it up, and keep the streets, bridges, water, power and sewers from falling apart while you do.</p>
    <p class="muted">The map is a made-up region stitched together from real places: a Boston-style peninsula and harbor, a Pittsburgh-style river confluence and steel heights, and a Nantucket-style island offshore.</p>
    <div class="choices">
      ${sv ? `<button class="choice primary" id="wContinue"><b>Continue</b><span>${saveLabel(sv)}</span></button>` : ""}
      <button class="choice ${sv ? "" : "primary"}" id="wGuided"><b>Guided start</b><span>Step-by-step orders with grants, and a calm first year with no random disasters. Recommended.</span></button>
      <button class="choice" id="wSandbox"><b>Sandbox</b><span>No tutorial. Storms, breaks and fires start on day one.</span></button>
    </div>
    <p class="muted small">${cloud ? "Your city saves to your claude.ai account automatically, so you can pick it up on any device." : "Your city saves automatically in this browser. Use Save → Export for a backup."}</p>`);
  const begin = guided => { if (sv) { saveTo("s3", { quiet: true }); } newGame({ guided, seed: 1 }); afterLoad(); if (guided) focusStep(); };
  if (sv) $("wContinue").onclick = () => { try { decodeState(sv); afterLoad(); } catch (e) { flash("That save couldn't be read"); newGame({ guided: true }); afterLoad(); } };
  $("wGuided").onclick = () => begin(true);
  $("wSandbox").onclick = () => begin(false);
}
function afterLoad() {
  closeModal(); sel = null; placing = null; setTool("inspect");
  if (!S.tut.on) centerOn(66, 38); else focusStep();
  buildTools(); buildOverlays(); renderNews(); renderInspector(); renderTutorial(); updateUI();
  running = true;
}

// ── input ────────────────────────────────────────────────────────────────────
const pointers = new Map();
let drag = null, pinch = null, lastPaint = -1;
const DRAG_TOOLS = new Set(["road", "ave", "hwy", "ramp", "tunnel", "R", "C", "I", "bulldoze", "levee", "repair"]);
function localXY(e) { const r = cv.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; }
function bindInput() {
  cv.addEventListener("pointerdown", e => {
    cv.setPointerCapture(e.pointerId);
    const [sx, sy] = localXY(e); pointers.set(e.pointerId, [sx, sy]);
    if (pointers.size === 2) { const [a, b] = [...pointers.values()]; pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), cx: (a[0] + b[0]) / 2, cy: (a[1] + b[1]) / 2 }; drag = null; return; }
    const panMode = tool === "inspect" || e.button === 1 || e.button === 2;
    drag = { sx, sy, cx: cam.x, cy: cam.y, pan: panMode, moved: false };
    if (!panMode) { const p = screenToTile(sx, sy); if (!p) return;
      if (tool === "place") return;
      if (TOOL[tool].proj) return;
      lastPaint = idx(p.x, p.y); doApply(p.x, p.y); }
  });
  cv.addEventListener("pointermove", e => {
    const [sx, sy] = localXY(e);
    if (pointers.has(e.pointerId)) pointers.set(e.pointerId, [sx, sy]);
    if (pinch && pointers.size === 2) {
      const [a, b] = [...pointers.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]), cx = (a[0] + b[0]) / 2, cy = (a[1] + b[1]) / 2;
      zoomAt(cx, cy, d / pinch.d); cam.x -= (cx - pinch.cx) / cam.z; cam.y -= (cy - pinch.cy) / cam.z; clampCam();
      pinch = { d, cx, cy }; return;
    }
    hover = screenToTile(sx, sy);
    if (!drag) return;
    if (Math.hypot(sx - drag.sx, sy - drag.sy) > 4) drag.moved = true;
    if (drag.pan) { cam.x = drag.cx - (sx - drag.sx) / cam.z; cam.y = drag.cy - (sy - drag.sy) / cam.z; clampCam(); cv.style.cursor = "grabbing"; return; }
    if (DRAG_TOOLS.has(tool) && hover && idx(hover.x, hover.y) !== lastPaint) { lastPaint = idx(hover.x, hover.y); doApply(hover.x, hover.y); }
  });
  const end = e => {
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinch = null;
    if (!drag) return;
    const [sx, sy] = localXY(e);
    if (drag.pan) { if (!drag.moved) { const p = screenToTile(sx, sy); if (p) { sel = p; renderInspector(); } } else S.counters.pan = (S.counters.pan || 0) + 1; cv.style.cursor = tool === "inspect" ? "grab" : "crosshair"; }
    else if (tool === "place" && !drag.moved) { const p = screenToTile(sx, sy); if (p) placeProject(p.x, p.y); }
    drag = null;
  };
  cv.addEventListener("pointerup", end); cv.addEventListener("pointercancel", end);
  cv.addEventListener("pointerleave", () => { if (!drag) hover = null; });
  cv.addEventListener("contextmenu", e => e.preventDefault());
  cv.addEventListener("wheel", e => { e.preventDefault(); const [sx, sy] = localXY(e); zoomAt(sx, sy, Math.exp(-e.deltaY * 0.0015)); }, { passive: false });
  $("minimap").addEventListener("pointerdown", e => { const r = e.target.getBoundingClientRect(); centerOn((e.clientX - r.left) / r.width * W, (e.clientY - r.top) / r.height * H); S.counters.pan = (S.counters.pan || 0) + 1; });

  document.addEventListener("click", e => {
    const b = e.target.closest("button, .wo-item"); if (!b) return;
    if (b.dataset.close != null) closeModal();
    else if (b.dataset.tool) { const t = TOOL[b.dataset.tool]; if (t.proj) startLandmark(t.id); else setTool(t.id); }
    else if (b.dataset.ov) { overlay = b.dataset.ov; if (overlay === "traffic") S.counters.sawTraffic = 1; buildOverlays(); }
    else if (b.dataset.sp != null) { speed = +b.dataset.sp; updateUI(); }
    else if (b.dataset.dispatch) { e.stopPropagation(); dispatch(+b.dataset.dispatch); updateUI(); }
    else if (b.dataset.repair) { const [x, y] = b.dataset.repair.split(",").map(Number); doApply(x, y, "repair"); renderInspector(); }
    else if (b.dataset.goto) { const [x, y] = b.dataset.goto.split(",").map(Number); sel = { x, y }; centerOn(x, y); renderInspector(); }
    else if (b.dataset.hire) { const [t, a, g] = b.dataset.hire.split("|"); hire(t, a, g || null); }
    else if (b.dataset.golfPick) { const [t, g] = b.dataset.golfPick.split("|"); archRFP(t, g); }
    else if (b.dataset.save) { saveTo(b.dataset.save).then(showSaves); }
    else if (b.dataset.load) { newestSave(b.dataset.load).then(sv => { try { decodeState(sv); afterLoad(); log("Save loaded.", "good"); } catch (err) { flash("That save couldn't be read"); } }); }
    else if (b.dataset.zoom) { zoomAt(viewW / 2, viewH / 2, b.dataset.zoom === "in" ? 1.3 : 1 / 1.3); }
  });
  $("tax").addEventListener("input", e => { S.tax = +e.target.value; computeStats(); renderBudget(); renderRCI(); });
  $("snowBudget").addEventListener("change", e => { S.snowBudget = e.target.checked; });
  $("bondBtn").addEventListener("click", () => { if (S.bonds.length >= 4) return; S.bonds.push({ left: 96 }); S.funds += 10000; log("Issued a $10,000 general obligation bond. Debt service is $150 a month."); updateUI(); });
  $("helpBtn").addEventListener("click", showHelp);
  $("saveBtn").addEventListener("click", showSaves);
  $("newBtn").addEventListener("click", () => {
    modal(`<h3>Start over?</h3><p>Your current city is copied to Slot 3 first, so you can come back to it.</p><div class="row"><button class="btn hv" id="mG">Guided start</button><button class="btn" id="mS">Sandbox</button><button class="btn ghost" data-close>Cancel</button></div>`);
    const go = g => saveTo("s3", { quiet: true }).then(() => { newGame({ guided: g, seed: 1 }); afterLoad(); });
    $("mG").onclick = () => go(true); $("mS").onclick = () => go(false);
  });
  $("placeCancel").addEventListener("click", () => setTool("inspect"));
  $("placeRotate").addEventListener("click", () => { if (placing) placing.rot ^= 1; });
  $("modal").addEventListener("click", e => { if (e.target.id === "modal" && running) closeModal(); });
  document.addEventListener("keydown", e => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    if (!$("modal").hidden) { if (e.key === "Escape" && running) closeModal(); return; }
    const k = e.key.toLowerCase(), step = 40 / cam.z;
    if (e.key === " ") { e.preventDefault(); speed = speed ? 0 : 1; updateUI(); return; }
    if (k === "arrowleft" || k === "a") { cam.x -= step; clampCam(); return; }
    if (k === "arrowright" || k === "d") { cam.x += step; clampCam(); return; }
    if (k === "arrowup" || k === "w") { e.preventDefault(); cam.y -= step; clampCam(); return; }
    if (k === "arrowdown" || k === "s") { e.preventDefault(); cam.y += step; clampCam(); return; }
    if (k === "+" || k === "=") { zoomAt(viewW / 2, viewH / 2, 1.25); return; }
    if (k === "-") { zoomAt(viewW / 2, viewH / 2, 0.8); return; }
    if (k === "o" && placing) { placing.rot ^= 1; return; }
    if (k === "escape") { setTool("inspect"); return; }
    const t = TOOLS.find(t => t.key === k); if (t && unlocked(t.id)) setTool(t.id);
  });
  window.addEventListener("resize", () => { resizeCanvas(); });
}
function doApply(x, y, id = tool) {
  apply(x, y, id);
  if (id !== "inspect") { sel = { x, y }; updateUI(); }
}

// ── loop ─────────────────────────────────────────────────────────────────────
let acc = 0, last = performance.now(), frameNo = 0, running = false;
function frame(now) {
  const dt = Math.min(250, now - last); last = now;
  if (running && speed && $("modal").hidden) {
    acc += dt * speed * 2 / 1000; let n = 0;
    while (acc >= 1 && n < 6) { acc -= 1; n++; day(); }
    if (n) updateUI();
  }
  if (S) { draw(now); if (frameNo++ % 20 === 0) drawMinimap(); }
  requestAnimationFrame(frame);
}
function boot() {
  cv = $("map"); ctx = cv.getContext("2d");
  newGame({ guided: true, seed: 1 });
  resizeCanvas(); centerOn(66, 36);
  buildTools(); buildOverlays(); bindInput(); renderNews(); renderInspector(); renderTutorial(); updateUI();
  requestAnimationFrame(frame);
  showWelcome();
  initCloud().then(() => { if (!running && cloud) showWelcome(); });
  setInterval(renderSaveStatus, 30000);
}
document.addEventListener("DOMContentLoaded", boot);
