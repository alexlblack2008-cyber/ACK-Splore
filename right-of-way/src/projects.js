"use strict";
// ─── Right-of-Way · landmarks, architects and their designs ─────────────────

let placing = null; // { type, arch, golf, rot }

const LABEL = { hall: "City Hall", airfield: "regional airfield", airport: "international airport", golf9: "9-hole country club", golf18: "18-hole country club" };
function footprint(type, rot) { const d = PROJ[type]; return rot ? [d.h, d.w] : [d.w, d.h]; }
function bid(type, archId, golfId) {
  const a = ARCH_BY[archId], g = golfId ? GOLF_BY[golfId] : null, base = TOOL[type].cost;
  const cost = g ? base * (0.7 * g.cost + 0.3 * a.cost) : base * a.cost;
  return { cost: Math.round(cost / 100) * 100, days: Math.round(PROJ[type].days * a.days), upkeep: Math.round(PROJ[type].upkeep * a.upkeep) };
}

// ── requests for proposals ───────────────────────────────────────────────────
function startLandmark(type) {
  if (!unlocked(type)) { flash(`Unlocks at ${TOOL[type].unlock.toLocaleString()} residents`); return; }
  if (type === "hall" && S.projects.some(p => p.type === "hall")) { flash(`${CITY} already has a City Hall`); return; }
  if (PROJ[type].holes) golfRFP(type); else archRFP(type, null);
}
function archRFP(type, golfId) {
  const d = PROJ[type], title = golfId ? "Step 2 of 2 · Clubhouse architect" : `Request for proposals · ${LABEL[type].replace(/^./, c => c.toUpperCase())}`;
  const cards = ARCH.map(a => {
    const b = bid(type, a.id, golfId);
    return `<article class="bid">
      <canvas class="pv" width="480" height="250" data-elev="${type}|${a.id}"></canvas>
      <div class="bid-h"><b>${a.firm}</b><span>${a.style}</span></div>
      <p>${a.pitch}</p>
      <dl class="kv">
        <dt>${golfId ? "Total bid, course and clubhouse" : "Bid"}</dt><dd>${money(b.cost)}</dd>
        <dt>Construction</dt><dd>${b.days} days</dd>
        <dt>Upkeep</dt><dd>${money(b.upkeep)}/mo</dd>
        <dt>Public approval</dt><dd>${a.approval > 0 ? "+" : ""}${a.approval}</dd>
        <dt>Visitor appeal</dt><dd>${stars(a.prestige)}</dd>
        <dt>Energy use</dt><dd>${Math.round(a.power * 100)}%</dd>
      </dl>
      <button class="btn hv" data-hire="${type}|${a.id}|${golfId || ""}" ${S.funds < b.cost ? "disabled" : ""}>${S.funds < b.cost ? "Can't afford" : "Hire " + a.firm.split(" ")[0]}</button>
    </article>`;
  }).join("");
  modal(`<h3>${title}</h3><p class="sub">${d.name === "Country club" ? "Four firms bid on the clubhouse. The course design you picked is included in each total." : `Four firms answered the city's RFP. Each bid covers design and construction. ${d.rpz ? "Airports need flat land, a street connection, and runway approaches clear of tall buildings." : ""}`}</p>
    <div class="bids">${cards}</div><div class="row"><button class="btn" data-close>Cancel</button></div>`, true);
  document.querySelectorAll("canvas[data-elev]").forEach(c => { const [t, a] = c.dataset.elev.split("|"); drawElevation(c, t, a); });
}
function golfRFP(type) {
  const d = PROJ[type];
  const cards = GOLF.map(g => `<article class="bid">
      <canvas class="pv" width="480" height="250" data-golf="${g.id}"></canvas>
      <div class="bid-h"><b>${g.firm}</b><span>${g.style}</span></div>
      <p>${g.pitch}</p>
      <dl class="kv">
        <dt>Course cost</dt><dd>${Math.round(g.cost * 100)}% of base</dd>
        <dt>Summer irrigation</dt><dd>${(d.water * g.water * 1.6).toFixed(2)} MGD</dd>
        <dt>Membership appeal</dt><dd>${stars(g.members)}</dd>
        <dt>Prestige</dt><dd>${stars(g.prestige)}</dd>
      </dl>
      <button class="btn hv" data-golf-pick="${type}|${g.id}">Choose ${g.firm.split(" ")[0]}</button>
    </article>`).join("");
  modal(`<h3>Step 1 of 2 · Golf course architect</h3><p class="sub">${d.holes} holes on a ${d.w}×${d.h} block site. Summer irrigation comes out of your water plants, so check your capacity first.</p>
    <div class="bids">${cards}</div><div class="row"><button class="btn" data-close>Cancel</button></div>`, true);
  document.querySelectorAll("canvas[data-golf]").forEach(c => drawGolfPreview(c, c.dataset.golf, d.holes));
}
const stars = v => "★".repeat(clamp(Math.round(v * 2.5), 1, 5)) + "☆".repeat(5 - clamp(Math.round(v * 2.5), 1, 5));
function hire(type, archId, golfId) {
  placing = { type, arch: archId, golf: golfId || null, rot: 0 };
  closeModal(); setTool("place");
  log(`Hired ${ARCH_BY[archId].firm}${golfId ? ` and ${GOLF_BY[golfId].firm}` : ""}. Pick a site for the ${LABEL[type]}.`);
}

// ── siting ───────────────────────────────────────────────────────────────────
function siteAt(hx, hy) { const [w, h] = footprint(placing.type, placing.rot); return { x: hx - Math.floor(w / 2), y: hy - Math.floor(h / 2), w, h }; }
function checkSite(hx, hy) {
  const { x, y, w, h } = siteAt(hx, hy), d = PROJ[placing.type];
  const b = bid(placing.type, placing.arch, placing.golf);
  let extra = 0, hills = 0, coast = false;
  for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) {
    if (!inb(xx, yy)) return [false, "Site runs off the map"];
    const t = T_(xx, yy);
    if (isWater(t.ter)) return [false, "Site includes water"];
    if (!freeLot(t)) return [false, "Site isn't clear"];
    if (t.ter === HILL) { hills++; if (d.flat) return [false, "Runways need flat land"]; if (!d.holes) extra += 100; }
    if (t.ter === FOREST) extra += 30;
    if (t.ter === MARSH) extra += 120;
    if (t.ter === BEACH || N4.some(([dx, dy]) => inb(xx + dx, yy + dy) && T_(xx + dx, yy + dy).ter === SEA)) coast = true;
  }
  const g = placing.golf && GOLF_BY[placing.golf];
  if (g && g.coast && !coast) return [false, "A links course must touch the ocean"];
  if (g && g.hill && hills < w * h * 0.25) return [false, `Needs 25% hillside (has ${Math.round(hills / (w * h) * 100)}%)`];
  if (d.rpz) for (const [rx, ry] of rpzTiles({ type: placing.type, x, y, w, h })) {
    const t = T_(rx, ry); if ((isZone(t) && t.lvl >= 2) || t.b === "proj" || isFacility(t)) return [false, "Tall buildings block the runway approach"];
  }
  if (!perimeter({ x, y, w, h }).some(([px, py]) => isLocal(T_(px, py)))) return [false, "Needs a street along one side"];
  return [true, b.cost + extra];
}
function placeProject(hx, hy) {
  const [ok, cost] = checkSite(hx, hy);
  if (!ok) { flash(cost); return; }
  if (S.funds < cost) { flash(`Need ${money(cost)}`); return; }
  const { x, y, w, h } = siteAt(hx, hy), d = PROJ[placing.type], b = bid(placing.type, placing.arch, placing.golf);
  S.funds -= cost;
  const p = { id: S.nextId++, type: placing.type, x, y, w, h, arch: placing.arch, golf: placing.golf, status: "build", prog: 0, days: b.days, name: projName(placing.type, x + w / 2, y + h / 2) };
  for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) { const t = T_(xx, yy); if (t.ter !== GRASS && t.ter !== HILL && t.ter !== BEACH) { t.ter = GRASS; terrainDirty = true; } clearTile(t); t.b = "proj"; t.pid = p.id; }
  S.projects.push(p);
  S.counters[p.type] = (S.counters[p.type] || 0) + 1;
  log(`Groundbreaking: ${p.name}. ${b.days} days to completion.`, "good");
  placing = null; setTool("inspect");
  markRPZ(); computeAll(); updateUI();
}
function projName(type, cx, cy) {
  if (type === "hall") return `${CITY} City Hall`;
  if (!PROJ[type].holes) return PROJ[type].name;
  let best = DISTRICTS[0], bd = Infinity;
  for (const d of DISTRICTS) { if (d.water) continue; const dd = Math.hypot(d.x - cx, d.y - cy); if (dd < bd) { bd = dd; best = d; } }
  const nm = best.name.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  return `${nm} Country Club`;
}
function confirmDemolish(pid) {
  const p = proj(pid); if (!p) return;
  modal(`<h3>Demolish ${p.name}?</h3><p>The whole ${p.w}×${p.h} site is cleared and nothing is refunded.</p><div class="row"><button class="btn hv" id="mYes">Demolish</button><button class="btn" data-close>Keep it</button></div>`);
  $("mYes").onclick = () => {
    for (let yy = p.y; yy < p.y + p.h; yy++) for (let xx = p.x; xx < p.x + p.w; xx++) clearTile(T_(xx, yy));
    S.projects = S.projects.filter(q => q !== p); markRPZ(); computeAll(); closeModal(); log(`${p.name} was demolished.`); updateUI();
  };
}

// ── drawing: elevations for the RFP cards ────────────────────────────────────
function drawElevation(cv, type, archId) {
  const c = cv.getContext("2d"), Wd = cv.width, Hd = cv.height, a = ARCH_BY[archId];
  c.fillStyle = "#EDF1F3"; c.fillRect(0, 0, Wd, Hd);
  c.fillStyle = "#DCE3D0"; c.fillRect(0, Hd * 0.8, Wd, Hd * 0.2);
  c.strokeStyle = "#1E2B38"; c.lineWidth = 2; c.beginPath(); c.moveTo(0, Hd * 0.8); c.lineTo(Wd, Hd * 0.8); c.stroke();
  const gy = Hd * 0.8;
  const tree = (x, s) => { c.fillStyle = "#6F8F5A"; c.beginPath(); c.arc(x, gy - s, s * 0.8, 0, 7); c.fill(); c.fillStyle = "#5A4A3A"; c.fillRect(x - 2, gy - s * 0.4, 4, s * 0.4); };
  tree(26, 26); tree(Wd - 30, 30);
  let bw, bh; if (type === "hall") { bw = 250; bh = 120; } else if (type === "airfield" || type === "airport") { bw = 330; bh = 60; } else { bw = 230; bh = 80; }
  const x0 = (Wd - bw) / 2, y0 = gy - bh;
  const [c1, c2, c3] = a.colors;
  const winGrid = (fill, rows, cols, pad) => { c.fillStyle = fill; const cw = (bw - pad * 2) / cols, rh = (bh - pad * 2) / rows;
    for (let r = 0; r < rows; r++) for (let k = 0; k < cols; k++) c.fillRect(x0 + pad + k * cw + cw * 0.25, y0 + pad + r * rh + rh * 0.2, cw * 0.5, rh * 0.55); };
  if (archId === "bulfinch") {
    c.fillStyle = c1; c.fillRect(x0, y0, bw, bh);
    winGrid(c2, type === "hall" ? 3 : 2, type === "hall" ? 9 : 12, 10);
    c.fillStyle = c2; c.fillRect(x0 - 6, y0 - 8, bw + 12, 10);
    if (type === "golf9" || type === "golf18") { c.fillStyle = "#3D3B38"; c.beginPath(); c.moveTo(x0 - 10, y0 - 6); c.lineTo(x0 + bw / 2, y0 - 50); c.lineTo(x0 + bw + 10, y0 - 6); c.fill(); }
    else { c.fillStyle = c2; c.beginPath(); c.moveTo(x0 + bw / 2 - 50, y0 - 8); c.lineTo(x0 + bw / 2, y0 - 34); c.lineTo(x0 + bw / 2 + 50, y0 - 8); c.fill(); }
    c.fillStyle = c2; c.fillRect(x0 + bw / 2 - 12, y0 - 58, 24, 26);
    c.fillStyle = c3; c.beginPath(); c.arc(x0 + bw / 2, y0 - 58, 14, Math.PI, 0); c.fill(); c.fillRect(x0 + bw / 2 - 1.5, y0 - 84, 3, 14);
    c.fillStyle = c2; for (let k = 0; k < 4; k++) c.fillRect(x0 + bw / 2 - 42 + k * 26, y0 + bh - 46, 8, 46);
  } else if (archId === "morrow") {
    c.fillStyle = c1; c.fillRect(x0, y0 + 6, bw, bh - 6);
    c.strokeStyle = c2; c.lineWidth = 1.2; c.beginPath();
    for (let k = x0; k <= x0 + bw; k += 18) { c.moveTo(k, y0 + 6); c.lineTo(k, gy); }
    for (let k = y0 + 6; k <= gy; k += 22) { c.moveTo(x0, k); c.lineTo(x0 + bw, k); } c.stroke();
    c.fillStyle = "rgba(255,255,255,.35)"; c.beginPath(); c.moveTo(x0 + 20, gy); c.lineTo(x0 + 90, y0 + 6); c.lineTo(x0 + 120, y0 + 6); c.lineTo(x0 + 50, gy); c.fill();
    c.fillStyle = c3; c.fillRect(x0 - 40, y0 - 4, bw + 80, 10);
  } else if (archId === "ferro") {
    const steps = type === "hall" ? 4 : 2, sh = bh / (steps + 1);
    c.fillStyle = c1; c.fillRect(x0 + 40, gy - sh, bw - 80, sh);
    for (let s = 1; s <= steps; s++) { const over = s * 14; c.fillStyle = s % 2 ? c2 : c1; c.fillRect(x0 + 40 - over, gy - sh * (s + 1), bw - 80 + over * 2, sh);
      c.fillStyle = c3; for (let k = x0 + 46 - over; k < x0 + bw - 46 + over; k += 12) c.fillRect(k, gy - sh * (s + 1) + sh * 0.3, 5, sh * 0.5); }
  } else {
    c.fillStyle = c1; c.fillRect(x0, y0 + 10, bw, bh - 10);
    c.strokeStyle = "rgba(60,40,20,.35)"; c.lineWidth = 1; c.beginPath(); for (let k = x0 + 4; k < x0 + bw; k += 6) { c.moveTo(k, y0 + 10); c.lineTo(k, gy); } c.stroke();
    c.fillStyle = "#EAF0EA"; for (let k = 0; k < 5; k++) c.fillRect(x0 + 16 + k * (bw - 32) / 5, y0 + 26, (bw - 32) / 5 - 12, bh - 44);
    c.fillStyle = c2; c.fillRect(x0 - 6, y0, bw + 12, 12);
    c.fillStyle = c3; for (let k = 0; k < 6; k++) { c.beginPath(); c.moveTo(x0 + 10 + k * 36, y0); c.lineTo(x0 + 34 + k * 36, y0 - 14); c.lineTo(x0 + 38 + k * 36, y0); c.fill(); }
  }
  if (type === "airfield" || type === "airport") {
    const tx = x0 + bw + 26; c.fillStyle = archId === "ferro" ? c2 : "#E4E7EA"; c.fillRect(tx, gy - 110, 14, 110);
    c.fillStyle = archId === "morrow" ? c1 : "#1E2B38"; c.fillRect(tx - 10, gy - 128, 34, 20); c.fillStyle = "#8FB3C9"; c.fillRect(tx - 7, gy - 124, 28, 8);
    c.fillStyle = "#1E2B38"; c.beginPath(); c.moveTo(40, 40); c.lineTo(78, 34); c.lineTo(86, 26); c.lineTo(90, 34); c.lineTo(100, 36); c.lineTo(90, 38); c.lineTo(80, 46); c.lineTo(76, 39); c.closePath(); c.fill();
  }
  c.fillStyle = "#1E2B38"; c.font = "600 15px 'Overpass Mono', monospace"; c.textAlign = "left"; c.fillText(`${a.style.toUpperCase()} · FRONT ELEVATION`, 14, 22);
}
function drawGolfPreview(cv, golfId, holes) {
  const c = cv.getContext("2d");
  paintGolf(c, 0, 0, cv.width, cv.height, cv.width / 15, golfId, 7, holes, "bulfinch");
  c.fillStyle = "rgba(30,43,56,.85)"; c.fillRect(0, 0, 250, 30); c.fillStyle = "#fff"; c.font = "600 15px 'Overpass Mono', monospace"; c.fillText(`ROUTING PLAN · ${GOLF_BY[golfId].style.toUpperCase()}`, 12, 21);
}
// Shared by the preview and the map: fairways, greens and hazards inside a box.
function paintGolf(c, ox, oy, w, h, unit, golfId, seed, holes, archId) {
  const rnd = mulberry32(seed * 131 + holes);
  const pal = { dunmore: ["#C9C79A", "#B8D38F", "#E9DCAE"], whitcombe: ["#8DBF72", "#B5DB8E", "#E8D9A8"], heather: ["#A7AE84", "#BFD89A", "#E8DDB5"], ridgeline: ["#93B77A", "#B5DB8E", "#E8D9A8"] }[golfId];
  c.fillStyle = pal[0]; c.fillRect(ox, oy, w, h);
  for (let k = 0; k < w * h / (unit * unit) * 0.6; k++) {
    const x = ox + rnd() * w, y = oy + rnd() * h, r = unit * (0.2 + rnd() * 0.4);
    c.fillStyle = golfId === "heather" ? "rgba(150,110,160,.45)" : golfId === "dunmore" ? "rgba(214,196,140,.8)" : "rgba(70,110,60,.55)";
    c.beginPath(); c.arc(x, y, r, 0, 7); c.fill();
  }
  if (golfId === "whitcombe") { c.fillStyle = "#86B7C8"; c.beginPath(); c.ellipse(ox + w * 0.55, oy + h * 0.5, unit * 1.3, unit * 0.8, 0.4, 0, 7); c.fill(); }
  if (golfId === "ridgeline") { c.strokeStyle = "rgba(90,70,40,.35)"; c.lineWidth = 1; for (let k = 1; k < 5; k++) { c.beginPath(); c.ellipse(ox + w * 0.3, oy + h * 0.6, k * unit * 1.2, k * unit * 0.8, 0.3, 0, 7); c.stroke(); } }
  const pad = unit * 0.9, pts = [];
  let px = ox + pad + unit, py = oy + h - pad - unit;
  for (let i = 0; i < holes; i++) {
    let nx, ny, tries = 0;
    do { const ang = rnd() * Math.PI * 2, len = unit * (2.2 + rnd() * 2.6); nx = px + Math.cos(ang) * len; ny = py + Math.sin(ang) * len; }
    while ((nx < ox + pad || ny < oy + pad || nx > ox + w - pad || ny > oy + h - pad || pts.some(p => Math.hypot(p[2] - nx, p[3] - ny) < unit * 1.3)) && ++tries < 40);
    if (tries >= 40) { nx = ox + pad + rnd() * (w - pad * 2); ny = oy + pad + rnd() * (h - pad * 2); }
    pts.push([px, py, nx, ny]); px = nx + (rnd() - 0.5) * unit; py = ny + (rnd() - 0.5) * unit;
    px = clamp(px, ox + pad, ox + w - pad); py = clamp(py, oy + pad, oy + h - pad);
  }
  c.lineCap = "round";
  for (const [x1, y1, x2, y2] of pts) { c.strokeStyle = pal[1]; c.lineWidth = unit * 0.85; c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke(); }
  for (const [x1, y1, x2, y2] of pts) {
    c.fillStyle = "#5FA64E"; c.beginPath(); c.arc(x2, y2, unit * 0.45, 0, 7); c.fill();
    c.fillStyle = pal[2]; c.beginPath(); c.ellipse(x2 + unit * 0.55, y2 - unit * 0.2, unit * 0.25, unit * 0.16, 0, 0, 7); c.fill();
    c.fillStyle = "#6A7F55"; c.fillRect(x1 - unit * 0.15, y1 - unit * 0.15, unit * 0.3, unit * 0.3);
    c.strokeStyle = "#1E2B38"; c.lineWidth = Math.max(0.6, unit * 0.05); c.beginPath(); c.moveTo(x2, y2); c.lineTo(x2, y2 - unit * 0.6); c.stroke();
    c.fillStyle = "#E8590C"; c.fillRect(x2, y2 - unit * 0.6, unit * 0.25, unit * 0.15);
  }
  const a = ARCH_BY[archId]; c.fillStyle = a.colors[0]; c.fillRect(ox + pad * 0.3, oy + h - unit * 1.6, unit * 1.4, unit * 1.2);
  c.fillStyle = a.colors[1]; c.fillRect(ox + pad * 0.3, oy + h - unit * 1.6, unit * 1.4, unit * 0.25);
}

// ── drawing: landmarks on the map ────────────────────────────────────────────
function drawProject(c, p, now) {
  const x0 = p.x * TS, y0 = p.y * TS, w = p.w * TS, h = p.h * TS, a = ARCH_BY[p.arch];
  if (p.status === "build") {
    c.fillStyle = "#B89F7E"; c.fillRect(x0, y0, w, h);
    c.save(); c.beginPath(); c.rect(x0, y0, w, h); c.clip();
    c.strokeStyle = "rgba(90,70,40,.35)"; c.lineWidth = 1; c.beginPath(); for (let k = -h; k < w; k += 8) { c.moveTo(x0 + k, y0 + h); c.lineTo(x0 + k + h, y0); } c.stroke(); c.restore();
    const cx = x0 + w * 0.3, cy = y0 + h * 0.6;
    c.strokeStyle = "#E0B43A"; c.lineWidth = 2; c.beginPath(); c.moveTo(cx, cy); c.lineTo(cx, cy - TS * 1.2); c.moveTo(cx - TS * 0.5, cy - TS * 1.2);
    c.lineTo(cx + TS * 1.8 * Math.cos(now / 3000), cy - TS * 1.2 + TS * 0.2 * Math.sin(now / 3000)); c.stroke();
    c.fillStyle = "rgba(30,43,56,.85)"; c.fillRect(x0 + 3, y0 + h - 9, w - 6, 6); c.fillStyle = "#E8590C"; c.fillRect(x0 + 4, y0 + h - 8, (w - 8) * p.prog / p.days, 4);
    return;
  }
  if (p.golf) { c.save(); c.beginPath(); c.rect(x0, y0, w, h); c.clip(); paintGolf(c, x0, y0, w, h, TS, p.golf, p.id, PROJ[p.type].holes, p.arch); c.restore(); }
  else if (p.type === "hall") {
    c.fillStyle = "#DAD5C8"; c.fillRect(x0, y0, w, h);
    c.fillStyle = "rgba(30,43,56,.3)"; c.fillRect(x0 + 6, y0 + 6, w - 9, h - 9);
    c.fillStyle = a.colors[0]; c.fillRect(x0 + 4, y0 + 4, w - 9, h - 9);
    if (p.arch === "morrow") { c.strokeStyle = a.colors[1]; c.lineWidth = 1; c.beginPath(); for (let k = x0 + 8; k < x0 + w - 5; k += 5) { c.moveTo(k, y0 + 4); c.lineTo(k, y0 + h - 5); } c.stroke(); }
    if (p.arch === "greenline") { c.fillStyle = a.colors[1]; c.fillRect(x0 + 8, y0 + 8, w - 17, h - 17); c.fillStyle = a.colors[2]; for (let k = 0; k < 3; k++) c.fillRect(x0 + 10, y0 + 11 + k * 9, w - 21, 4); }
    if (p.arch === "ferro") { c.fillStyle = a.colors[1]; c.fillRect(x0 + 9, y0 + 9, w - 19, h - 19); c.fillStyle = a.colors[2]; c.fillRect(x0 + 15, y0 + 15, w - 31, h - 31); }
    if (p.arch === "bulfinch") { c.strokeStyle = a.colors[1]; c.lineWidth = 2; c.strokeRect(x0 + 6, y0 + 6, w - 13, h - 13); c.fillStyle = a.colors[2]; c.beginPath(); c.arc(x0 + w / 2 - 1, y0 + h / 2 - 1, 6, 0, 7); c.fill(); }
  } else {
    const horiz = p.w >= p.h, runways = p.type === "airport" ? 2 : 1;
    c.fillStyle = "#C9D4BC"; c.fillRect(x0, y0, w, h);
    const across = horiz ? h : w;
    for (let r = 0; r < runways; r++) {
      const off = runways === 1 ? across * 0.35 : across * (r === 0 ? 0.18 : 0.82);
      const rw = TS * 0.9;
      c.fillStyle = "#3E4349";
      if (horiz) c.fillRect(x0 + 4, y0 + off - rw / 2, w - 8, rw); else c.fillRect(x0 + off - rw / 2, y0 + 4, rw, h - 8);
      c.strokeStyle = "#F5F6F1"; c.lineWidth = 1.2; c.setLineDash([6, 5]); c.beginPath();
      if (horiz) { c.moveTo(x0 + 14, y0 + off); c.lineTo(x0 + w - 14, y0 + off); } else { c.moveTo(x0 + off, y0 + 14); c.lineTo(x0 + off, y0 + h - 14); }
      c.stroke(); c.setLineDash([]);
      c.fillStyle = "#F5F6F1";
      for (let k = -2; k <= 2; k++) { if (horiz) { c.fillRect(x0 + 6, y0 + off + k * 2.6 - 0.8, 6, 1.6); c.fillRect(x0 + w - 12, y0 + off + k * 2.6 - 0.8, 6, 1.6); }
        else { c.fillRect(x0 + off + k * 2.6 - 0.8, y0 + 6, 1.6, 6); c.fillRect(x0 + off + k * 2.6 - 0.8, y0 + h - 12, 1.6, 6); } }
    }
    const tOff = runways === 1 ? across * 0.72 : across * 0.5, depth = TS * (runways === 1 ? 0.7 : 1.6), len = (horiz ? w : h) * 0.45;
    c.fillStyle = "#9097A0";
    if (horiz) c.fillRect(x0 + w * 0.28, y0 + tOff - depth, len, depth * 0.7); else c.fillRect(x0 + tOff - depth, y0 + h * 0.28, depth * 0.7, len);
    c.fillStyle = a.colors[0];
    if (horiz) c.fillRect(x0 + w * 0.3, y0 + tOff - depth * 0.2, len * 0.9, depth * 0.8); else c.fillRect(x0 + tOff - depth * 0.2, y0 + h * 0.3, depth * 0.8, len * 0.9);
    c.fillStyle = "#1E2B38"; const tx = horiz ? x0 + w * 0.2 : x0 + tOff, ty = horiz ? y0 + tOff : y0 + h * 0.2;
    c.beginPath(); c.arc(tx, ty, 3.5, 0, 7); c.fill();
  }
  if (!p.pw || !p.wt) { c.fillStyle = "#BF3A2B"; c.beginPath(); c.arc(x0 + w - 6, y0 + 6, 4, 0, 7); c.fill(); }
}
function drawRPZ(c, p) {
  c.fillStyle = "rgba(191,58,43,.12)"; c.strokeStyle = "rgba(191,58,43,.5)"; c.setLineDash([3, 3]); c.lineWidth = 1;
  for (const [x, y] of rpzTiles(p)) { c.fillRect(x * TS, y * TS, TS, TS); }
  c.setLineDash([]);
}
