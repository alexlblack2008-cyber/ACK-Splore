"use strict";
// ─── Right-of-Way · guided start ────────────────────────────────────────────
// A short run of orders from the Mayor's office. Each step points at a tool
// and a place on the map, checks itself off, and pays a small grant.

const STEPS = [
  { title: "Fix the water main", reward: 1000, tool: null, at: () => S.flags.brk,
    text: "A main broke at the Neck, the only land link into Old Bayford. The whole peninsula is short on water. Open Work Orders on the right and press Dispatch.",
    done: () => !S.inc.some(i => i.kind === "main" && i.x === S.flags.brk[0] && i.y === S.flags.brk[1] && i.status === "open") },
  { title: "Get your bearings", reward: 500, tool: "inspect", at: () => [45, 40],
    text: "Scroll or pinch to zoom. With Inspect selected, drag to pan. The minimap on the right jumps anywhere. The peninsula is Old Bayford; the land north of the harbor is Northbank.",
    done: () => (S.counters.zoom || 0) + (S.counters.pan || 0) >= 3 },
  { title: "Open up Northbank", reward: 1500, tool: "road", at: () => [70, 23],
    text: "Northbank is empty land across the Old Harbor Bridge. Lay at least 8 street tiles off the street that's already there (drag to draw a run).",
    done: () => (S.counters.road || 0) >= 8 },
  { title: "Zone new housing", reward: 1500, tool: "R", at: () => [70, 21],
    text: "Zone at least 10 residential tiles along your new streets. Houses need a street on one side plus power and water.",
    done: () => (S.counters.R || 0) >= 10 },
  { title: "Treat the sewage", reward: 2500, tool: "sewage", at: () => [75, 42],
    text: "Bayford pumps raw sewage into the harbor, and the state fines you every month it does. Build a sewage plant on the shore where it can reach your streets.",
    done: () => S.tiles.some(t => t.b === "sewage" && t.link) },
  { title: "Check the traffic", reward: 500, tool: null, at: () => [68, 37],
    text: "Switch the map layer to Traffic LOS above the map. Green streets flow freely. Orange and red ones are near or over capacity (LOS E and F).",
    done: () => !!S.counters.sawTraffic },
  { title: "Save the Old Harbor Bridge", reward: 2000, tool: "repair", at: () => S.flags.bridge,
    text: "The 1890s bridge to Northbank is rated poor. Below NBI 3 it closes; left alone after that, it collapses. Use Repair on each bridge span now while it's cheap.",
    done: () => { let n = 0, ok = 0; for (let y = 24; y <= 33; y++) { const t = T_(70, y); if (isBridge(t)) { n++; if (t.cond > 80) ok++; } } return n > 0 && ok === n; } },
  { title: "Hire a maintenance crew", reward: 1500, tool: "depot", at: () => [66, 39],
    text: "Build a Works depot. It adds a second crew and patches roads within 8 tiles before they fail, for about a third of the emergency price.",
    done: () => S.tiles.some(t => t.b === "depot") },
  { title: "Commission a City Hall", reward: 3000, tool: "hall", at: () => [60, 47],
    text: "Pick City Hall under Landmarks. Four architects will pitch different designs with different costs, build times, upkeep and public reaction. Hire one, then pick a site next to a street.",
    done: () => S.projects.some(p => p.type === "hall") },
  { title: "Grow to 1,000 residents", reward: 4000, tool: "R", at: () => [52, 44],
    text: "Keep zoning, keep the utilities ahead of demand, and fix what breaks. The zoning demand bars show what people want built.",
    done: () => S.pop >= 1000 },
  { title: "Tame an intersection", reward: 1500, tool: "signal", at: () => [68, 38],
    text: "Busy four-way crossings without control drop to 60% capacity and cause crashes. Put a traffic signal or a roundabout on one.",
    done: () => S.tiles.some(t => t.ctl) },
  { title: "Open an airfield", reward: 8000, tool: "airfield", at: () => [86, 31],
    text: "At 1,500 residents the FAA will fund a regional airfield. East Flats is flat marsh near the harbor. The runway approaches must stay clear of tall buildings.",
    done: () => S.projects.some(p => p.type === "airfield" || p.type === "airport") },
  { title: "Tee off", reward: 8000, tool: "golf9", at: () => [26, 12],
    text: "At 2,000 residents you can build a country club. Brookfield's rolling woods suit a parkland course; the South Shore beaches suit a links. Nearby land values will jump.",
    done: () => S.projects.some(p => p.golf) },
];

function tutStep() { return S.tut.on ? STEPS[S.tut.step] : null; }
function checkTutorial() {
  const st = tutStep(); if (!st) return;
  if (st.done()) {
    S.funds += st.reward; S.tut.done.push(S.tut.step);
    log(`Order complete: ${st.title}. Grant of ${money(st.reward)}.`, "good");
    S.tut.step++;
    if (S.tut.step >= STEPS.length) { S.tut.on = false; log("That's every order from the Mayor's office. Bayford is yours to run.", "good"); }
    else focusStep();
    renderTutorial();
  }
}
function focusStep() {
  const st = tutStep(); if (!st) return;
  const at = st.at && st.at(); if (at) centerOn(at[0], at[1]);
  document.querySelectorAll(".tool.pulse").forEach(b => b.classList.remove("pulse"));
  if (st.tool) { const b = document.querySelector(`.tool[data-tool="${st.tool}"]`); if (b) b.classList.add("pulse"); }
}
function renderTutorial() {
  const box = $("tutPanel"); if (!box) return;
  const st = tutStep();
  box.hidden = !st;
  if (!st) { document.querySelectorAll(".tool.pulse").forEach(b => b.classList.remove("pulse")); return; }
  $("tutCount").textContent = `${S.tut.step + 1} of ${STEPS.length}`;
  $("tutBody").innerHTML = `<h3>${st.title}</h3><p>${st.text}</p>
    <div class="row"><span class="status-pill">Grant ${money(st.reward)}</span><button class="btn" id="tutShow">Show me</button><button class="btn ghost" id="tutSkip">Skip tutorial</button></div>
    <ol class="tut-list">${STEPS.map((s, i) => `<li class="${i < S.tut.step ? "done" : i === S.tut.step ? "now" : ""}">${s.title}</li>`).join("")}</ol>`;
  $("tutShow").onclick = () => { focusStep(); const st2 = tutStep(); if (st2 && st2.tool) { if (TOOL[st2.tool].proj) startLandmark(st2.tool); else setTool(st2.tool); } };
  $("tutSkip").onclick = () => { S.tut.on = false; renderTutorial(); log("Tutorial skipped. Random events are now on."); };
}
function drawTutorialTarget(now) {
  const st = tutStep(); if (!st || !st.at) return;
  const at = st.at(); if (!at) return;
  const r = (10 + ((now / 30) % 18)) / Math.min(1.5, cam.z);
  ctx.strokeStyle = `rgba(232,89,12,${1 - ((now / 30) % 18) / 18})`; ctx.lineWidth = 2 / cam.z;
  ctx.beginPath(); ctx.arc(at[0] * TS + TS / 2, at[1] * TS + TS / 2, r, 0, 7); ctx.stroke();
}
