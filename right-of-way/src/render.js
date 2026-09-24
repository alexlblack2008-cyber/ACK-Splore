"use strict";
// ─── Right-of-Way · map rendering, camera and minimap ───────────────────────

let terrainDirty = true, terCanvas = null;
const cam = { x: 60 * TS, y: 26 * TS, z: 1.6 };
let cv, ctx, dpr = 1, viewW = 800, viewH = 560;
let overlay = "base", hover = null, sel = null, flashMsg = null;

const COL = {
  grass: "#DCE3D0", grass2: "#D6DDC9", forest: "#B7C9A0", tree: "#8FAA78", sea: "#86B1C4", fresh: "#95C0CC", shore: "#5E8FA6",
  hill: "#D3CDB2", marsh: "#C3CEA8", reed: "#93A57A", beach: "#EADFB8",
  road: "#6E737A", ave: "#4A4E55", hwy: "#2F3A48", ramp: "#5B6B7E", bridge: "#8B7E6B", lane: "#F5F6F1", yellow: "#F2C14E",
  R: "#EFD77A", C: "#E39A96", I: "#B4A2D6", Rb: "#C9A63A", Cb: "#B6544F", Ib: "#7A62A6", ink: "#1E2B38", hivis: "#E8590C",
  good: "#2F7D4F", warn: "#D69A12", bad: "#BF3A2B",
};
const LOS_COL = { A: "#2F7D4F", B: "#5E9C3A", C: "#A8A523", D: "#D69A12", E: "#D5661C", F: "#BF3A2B" };
function flash(msg) { if (msg) flashMsg = { msg: String(msg), until: performance.now() + 1500 }; }
function ramp(v) { v = clamp(v, 0, 1);
  const a = v < 0.5 ? [191, 58, 43] : [214, 154, 18], b = v < 0.5 ? [214, 154, 18] : [47, 125, 79], k = v < 0.5 ? v * 2 : (v - 0.5) * 2;
  return `rgb(${a.map((c, i) => Math.round(c + (b[i] - c) * k)).join(",")})`; }

// ── camera ───────────────────────────────────────────────────────────────────
function resizeCanvas() {
  const box = cv.parentElement.getBoundingClientRect();
  viewW = Math.max(200, box.width);
  viewH = Math.round(clamp(window.innerHeight * 0.68, 340, 780));
  if (window.innerWidth < 760) viewH = Math.round(clamp(window.innerHeight * 0.55, 300, 560));
  cv.style.height = viewH + "px";
  dpr = Math.min(2, window.devicePixelRatio || 1);
  cv.width = Math.round(viewW * dpr); cv.height = Math.round(viewH * dpr);
  clampCam();
}
const minZoom = () => Math.max(viewW / (W * TS), viewH / (H * TS));
function clampCam() {
  cam.z = clamp(cam.z, minZoom(), 4);
  cam.x = clamp(cam.x, 0, Math.max(0, W * TS - viewW / cam.z));
  cam.y = clamp(cam.y, 0, Math.max(0, H * TS - viewH / cam.z));
}
function zoomAt(sx, sy, f) {
  const wx = cam.x + sx / cam.z, wy = cam.y + sy / cam.z;
  cam.z = clamp(cam.z * f, minZoom(), 4);
  cam.x = wx - sx / cam.z; cam.y = wy - sy / cam.z; clampCam();
  S.counters.zoom = (S.counters.zoom || 0) + 1;
}
function centerOn(x, y) { cam.x = x * TS - viewW / cam.z / 2; cam.y = y * TS - viewH / cam.z / 2; clampCam(); }
function screenToTile(sx, sy) { const x = Math.floor((cam.x + sx / cam.z) / TS), y = Math.floor((cam.y + sy / cam.z) / TS); return inb(x, y) ? { x, y } : null; }

// ── terrain cache ────────────────────────────────────────────────────────────
function buildTerrain() {
  if (!terCanvas) { terCanvas = document.createElement("canvas"); terCanvas.width = W * TS; terCanvas.height = H * TS; }
  const c = terCanvas.getContext("2d");
  if (!S._elev) S._elev = elevations(S.seed);
  const E = S._elev;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const t = T_(x, y), px = x * TS, py = y * TS;
    switch (t.ter) {
      case SEA: c.fillStyle = COL.sea; break;
      case FRESH: c.fillStyle = COL.fresh; break;
      case HILL: c.fillStyle = `hsl(${40 - E[idx(x, y)] * 10}, 28%, ${78 - (E[idx(x, y)] - 0.57) * 40}%)`; break;
      case MARSH: c.fillStyle = COL.marsh; break;
      case BEACH: c.fillStyle = COL.beach; break;
      default: c.fillStyle = (x + y) % 2 ? COL.grass : COL.grass2;
    }
    c.fillRect(px, py, TS, TS);
    if (t.ter === FOREST) { c.fillStyle = COL.forest; c.fillRect(px, py, TS, TS); c.fillStyle = COL.tree;
      for (const [ox, oy] of [[4, 5], [11, 4], [7, 11], [13, 12]]) { c.beginPath(); c.arc(px + ox, py + oy, 2.6, 0, 7); c.fill(); } }
    if (t.ter === MARSH) { c.strokeStyle = COL.reed; c.lineWidth = 0.8; c.beginPath(); for (const ox of [3, 8, 13]) { c.moveTo(px + ox, py + 12); c.lineTo(px + ox + 1, py + 7); } c.stroke(); }
    if (t.ter === SEA && (x * 7 + y * 3) % 11 === 0) { c.strokeStyle = "rgba(255,255,255,.28)"; c.lineWidth = 1; c.beginPath(); c.moveTo(px + 3, py + 8); c.quadraticCurveTo(px + 6, py + 5, px + 9, py + 8); c.stroke(); }
  }
  // shorelines
  c.strokeStyle = COL.shore; c.lineWidth = 1.2; c.beginPath();
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    if (isWater(T_(x, y).ter)) continue;
    for (const [dx, dy] of N4) { const nx = x + dx, ny = y + dy; if (!inb(nx, ny) || !isWater(T_(nx, ny).ter)) continue;
      const px = x * TS, py = y * TS;
      if (dx === 1) { c.moveTo(px + TS, py); c.lineTo(px + TS, py + TS); } if (dx === -1) { c.moveTo(px, py); c.lineTo(px, py + TS); }
      if (dy === 1) { c.moveTo(px, py + TS); c.lineTo(px + TS, py + TS); } if (dy === -1) { c.moveTo(px, py); c.lineTo(px + TS, py); } }
  }
  c.stroke();
  // survey contours (marching squares on tile-corner elevations)
  const corner = (x, y) => { let s = 0, n = 0; for (const [dx, dy] of [[-1, -1], [0, -1], [-1, 0], [0, 0]]) { const tx = x + dx, ty = y + dy; if (inb(tx, ty)) { s += isWater(T_(tx, ty).ter) ? 0.2 : E[idx(tx, ty)]; n++; } } return s / n; };
  const cor = new Float32Array((W + 1) * (H + 1)); for (let y = 0; y <= H; y++) for (let x = 0; x <= W; x++) cor[y * (W + 1) + x] = corner(x, y);
  for (const L of [0.5, 0.58, 0.66, 0.74, 0.82, 0.9]) {
    c.strokeStyle = L >= 0.66 ? "rgba(120,92,52,.45)" : "rgba(120,110,70,.25)"; c.lineWidth = L === 0.66 || L === 0.82 ? 1.1 : 0.7; c.beginPath();
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const a = cor[y * (W + 1) + x], b = cor[y * (W + 1) + x + 1], d = cor[(y + 1) * (W + 1) + x], e2 = cor[(y + 1) * (W + 1) + x + 1];
      const pts = [], px = x * TS, py = y * TS, f = (p, q) => (L - p) / (q - p);
      if ((a < L) !== (b < L)) pts.push([px + f(a, b) * TS, py]);
      if ((b < L) !== (e2 < L)) pts.push([px + TS, py + f(b, e2) * TS]);
      if ((d < L) !== (e2 < L)) pts.push([px + f(d, e2) * TS, py + TS]);
      if ((a < L) !== (d < L)) pts.push([px, py + f(a, d) * TS]);
      if (pts.length >= 2) { c.moveTo(...pts[0]); c.lineTo(...pts[1]); if (pts.length === 4) { c.moveTo(...pts[2]); c.lineTo(...pts[3]); } }
    }
    c.stroke();
  }
  terrainDirty = false;
}

// ── features ─────────────────────────────────────────────────────────────────
function connects(a, b) { return isRoad(b) && ((a.b === "hwy") === (b.b === "hwy") || a.b === "ramp" || b.b === "ramp"); }
function drawRoad(c, t, x, y, now) {
  const px = x * TS, py = y * TS, h = TS / 2;
  const nb = N4.map(([dx, dy]) => inb(x + dx, y + dy) && connects(t, T_(x + dx, y + dy)));
  if (t.st === "tunnel") {
    c.strokeStyle = "rgba(47,58,72,.8)"; c.lineWidth = 1.2; c.setLineDash([3, 2]); c.beginPath();
    const vert = (nb[2] || nb[3]) && !(nb[0] || nb[1]);
    if (vert) { c.moveTo(px + 3, py); c.lineTo(px + 3, py + TS); c.moveTo(px + TS - 3, py); c.lineTo(px + TS - 3, py + TS); }
    else { c.moveTo(px, py + 3); c.lineTo(px + TS, py + 3); c.moveTo(px, py + TS - 3); c.lineTo(px + TS, py + TS - 3); }
    c.stroke(); c.setLineDash([]);
  } else {
    const col = COL[t.b];
    if (t.st === "bridge") {
      const vert = (nb[2] || nb[3]) && !(nb[0] || nb[1]);
      c.fillStyle = t.b === "road" ? COL.bridge : col;
      if (vert) c.fillRect(px + 2, py, TS - 4, TS); else c.fillRect(px, py + 2, TS, TS - 4);
      c.fillStyle = COL.ink; if (vert) { c.fillRect(px + 1.5, py, 1.2, TS); c.fillRect(px + TS - 2.7, py, 1.2, TS); } else { c.fillRect(px, py + 1.5, TS, 1.2); c.fillRect(px, py + TS - 2.7, TS, 1.2); }
    } else { c.fillStyle = col; c.fillRect(px, py, TS, TS); }
  }
  const lane = t.b === "hwy" ? "#DADDE0" : t.b === "ave" ? COL.yellow : COL.lane;
  c.strokeStyle = lane; c.lineWidth = t.b === "ave" || t.b === "hwy" ? 1.3 : 0.9; c.setLineDash(t.b === "ave" ? [] : [2.5, 2.5]);
  c.beginPath(); nb.forEach((on, k) => { if (on) { const [dx, dy] = N4[k]; c.moveTo(px + h, py + h); c.lineTo(px + h + dx * h, py + h + dy * h); } }); c.stroke(); c.setLineDash([]);
  if (t.ctl === "signal") { c.fillStyle = COL.ink; c.beginPath(); c.arc(px + TS - 3.5, py + 3.5, 2.8, 0, 7); c.fill(); const ph = Math.floor(now / 1500) % 2; c.fillStyle = ph ? "#4CAF50" : "#E0463A"; c.beginPath(); c.arc(px + TS - 3.5, py + 3.5, 1.6, 0, 7); c.fill(); }
  if (t.ctl === "round") { c.fillStyle = COL[t.b]; c.beginPath(); c.arc(px + h, py + h, 7, 0, 7); c.fill(); c.fillStyle = "#9DB39A"; c.beginPath(); c.arc(px + h, py + h, 3.5, 0, 7); c.fill(); }
  if (t.cond < 45 && !t.sink && overlay === "base" && !t.st) { c.fillStyle = "rgba(20,20,20,.55)"; for (let k = 0; k < (t.cond < 25 ? 3 : 1); k++) { const hh = hash(x + k, y * 3 + k); c.beginPath(); c.arc(px + 3 + hh * 10, py + 3 + ((hh * 97) % 1) * 10, 1.3, 0, 7); c.fill(); } }
  if (t.sink) { c.fillStyle = "#2B2118"; c.beginPath(); c.ellipse(px + h, py + h, 5.5, 4.5, 0.3, 0, 7); c.fill(); }
  if (t.closed) { c.strokeStyle = COL.hivis; c.lineWidth = 1.6; c.beginPath(); for (let k = -TS; k < TS; k += 5) { c.moveTo(px + Math.max(0, k), py + Math.max(0, -k)); c.lineTo(px + Math.min(TS, k + TS), py + Math.min(TS, TS - k)); } c.stroke(); }
  if (t.fW) { c.fillStyle = "rgba(80,170,220,.85)"; c.beginPath(); c.arc(px + h, py + h, 4 + Math.sin(now / 150) * 1.2, 0, 7); c.fill(); }
  if (t.fP) { c.strokeStyle = COL.yellow; c.lineWidth = 1.6; c.beginPath(); c.moveTo(px + 5, py + 3); c.lineTo(px + 9, py + 8); c.lineTo(px + 6, py + 9); c.lineTo(px + 11, py + 14); c.stroke(); }
}
function drawZone(c, t, x, y, now) {
  const px = x * TS, py = y * TS;
  c.fillStyle = COL[t.b]; c.globalAlpha = 0.55; c.fillRect(px + 1, py + 1, TS - 2, TS - 2); c.globalAlpha = 1;
  if (!t.lvl) { c.strokeStyle = COL[t.b + "b"]; c.lineWidth = 0.8; c.setLineDash([2, 2]); c.strokeRect(px + 2, py + 2, TS - 4, TS - 4); c.setLineDash([]); return; }
  const inset = [0, 4, 2.5, 1.2][t.lvl];
  c.fillStyle = "rgba(30,43,56,.25)"; c.fillRect(px + inset + 1.2, py + inset + 1.2, TS - inset * 2, TS - inset * 2);
  c.fillStyle = t.b === "R" && t.lvl === 3 && t.val > 1.6 ? "#B58A2A" : COL[t.b + "b"]; c.fillRect(px + inset, py + inset, TS - inset * 2, TS - inset * 2);
  c.fillStyle = "rgba(255,255,255,.35)";
  if (t.lvl === 3) for (let k = 0; k < 3; k++) c.fillRect(px + 3, py + 3 + k * 3.6, TS - 6, 1.2);
  if (t.lvl === 2) c.fillRect(px + 4, py + 4, TS - 8, 1.6);
  if (t.fire) { const f = 0.5 + Math.sin(now / 90 + px) * 0.3; c.fillStyle = `rgba(232,89,12,${f})`; c.fillRect(px + 2, py + 2, TS - 4, TS - 4); c.fillStyle = "rgba(255,210,80,.9)"; c.beginPath(); c.moveTo(px + TS / 2, py + 2); c.lineTo(px + 12, py + 13); c.lineTo(px + 4, py + 13); c.fill(); }
  if ((!t.pw || !t.wt) && overlay === "base") { c.fillStyle = COL.bad; c.beginPath(); c.arc(px + TS - 3, py + 3, 2.4, 0, 7); c.fill(); }
}
function drawFacility(c, t, x, y) {
  const px = x * TS, py = y * TS, tl = TOOL[t.b];
  if (t.b === "park") { c.fillStyle = "#A9CC8F"; c.fillRect(px + 1, py + 1, TS - 2, TS - 2); c.fillStyle = "#5F8F4E"; for (const [ox, oy] of [[5, 5], [11, 7], [6, 11]]) { c.beginPath(); c.arc(px + ox, py + oy, 2.5, 0, 7); c.fill(); } return; }
  if (t.b === "levee") { c.fillStyle = "#A78B63"; c.fillRect(px, py, TS, TS); c.strokeStyle = "#7D6545"; c.lineWidth = 0.8; c.beginPath(); for (let k = 3; k < TS; k += 3.5) { c.moveTo(px + k, py + 2); c.lineTo(px + k - 2, py + TS - 2); } c.stroke(); return; }
  c.fillStyle = "rgba(30,43,56,.3)"; c.fillRect(px + 2, py + 2, TS - 2.5, TS - 2.5);
  c.fillStyle = tl.sw; c.fillRect(px + 1, py + 1, TS - 2.5, TS - 2.5);
  c.strokeStyle = COL.ink; c.lineWidth = 1; c.strokeRect(px + 1.5, py + 1.5, TS - 3.5, TS - 3.5);
  c.fillStyle = t.b === "depot" ? "#fff" : COL.ink; c.font = `800 ${tl.glyph.length > 2 ? 5.5 : 7}px Overpass, sans-serif`; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText(tl.glyph, px + TS / 2 - 0.5, py + TS / 2 + 0.5);
  if (t.off || t.link === false || t.salt) { c.strokeStyle = COL.bad; c.lineWidth = 1.8; c.beginPath(); c.moveTo(px + 2, py + 2); c.lineTo(px + TS - 2, py + TS - 2); c.stroke(); }
}

// ── overlays ─────────────────────────────────────────────────────────────────
function overlayColor(t) {
  if (overlay === "cond") return isRoad(t) ? ramp(t.cond / 100) : null;
  if (overlay === "traffic") return isRoad(t) ? (t.load < 1 ? "#9AA0A6" : LOS_COL[los(vcOf(t))]) : null;
  if (overlay === "value") return !isWater(t.ter) && !isRoad(t) ? ramp((t.val - 0.4) / 1.8) : null;
  const m = { power: ["power", "pw", "fP", "power"], water: ["water", "wt", "fW", "pump"], sewer: ["sewer", "sw", null, "sewage"] }[overlay];
  if (!m) return null;
  if (isRoad(t)) { const r = t["r_" + m[0]]; return (m[2] && t[m[2]]) || t.sink ? COL.hivis : r <= 0 ? "#9AA0A6" : ramp(r); }
  if (isZone(t) && t.lvl) return t[m[1]] ? "#3F7CAC" : COL.bad;
  if (t.b === m[3]) return t.off || !t.link ? COL.bad : COL.ink;
  if (t.b === "proj") { const p = proj(t.pid); return p && p.status === "open" ? (p[m[1]] ? "#3F7CAC" : COL.bad) : null; }
  return null;
}

// ── frame ────────────────────────────────────────────────────────────────────
function draw(now) {
  if (terrainDirty) buildTerrain();
  const z = cam.z;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = COL.sea; ctx.fillRect(0, 0, viewW, viewH);
  ctx.setTransform(dpr * z, 0, 0, dpr * z, -cam.x * z * dpr, -cam.y * z * dpr);
  ctx.imageSmoothingEnabled = z < 1;
  ctx.drawImage(terCanvas, 0, 0);
  const x0 = Math.max(0, Math.floor(cam.x / TS) - 1), y0 = Math.max(0, Math.floor(cam.y / TS) - 1);
  const x1 = Math.min(W - 1, Math.ceil((cam.x + viewW / z) / TS) + 1), y1 = Math.min(H - 1, Math.ceil((cam.y + viewH / z) / TS) + 1);
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
    const t = T_(x, y);
    if (t.flood) { ctx.fillStyle = `rgba(90,150,180,${0.2 + t.flood * 0.07})`; ctx.fillRect(x * TS, y * TS, TS, TS); }
    if (!t.b || t.b === "proj") continue;
    if (isRoad(t)) drawRoad(ctx, t, x, y, now); else if (isZone(t)) drawZone(ctx, t, x, y, now); else drawFacility(ctx, t, x, y);
  }
  for (const p of S.projects) {
    if (p.x > x1 || p.y > y1 || p.x + p.w < x0 || p.y + p.h < y0) continue;
    drawProject(ctx, p, now);
    if (PROJ[p.type].rpz && (overlay === "value" || (placing && PROJ[placing.type].rpz))) drawRPZ(ctx, p);
  }
  if (overlay !== "base") {
    ctx.fillStyle = "rgba(230,234,225,.5)"; ctx.fillRect(x0 * TS, y0 * TS, (x1 - x0 + 1) * TS, (y1 - y0 + 1) * TS);
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) { const col = overlayColor(T_(x, y)); if (col) { ctx.fillStyle = col; ctx.fillRect(x * TS + 1.5, y * TS + 1.5, TS - 3, TS - 3); } }
  }
  // work order markers
  const pulse = (Math.sin(now / 220) + 1) / 2;
  for (const i of S.inc) {
    if (i.status === "done") continue;
    const cx = i.x * TS + TS / 2, cy = i.y * TS + TS / 2, s = (i.status === "open" ? 6 + pulse * 2.5 : 5.5) / Math.min(1, z) ;
    ctx.fillStyle = i.status === "crew" ? COL.ink : i.status === "auto" ? "#5B6B7E" : COL.hivis; ctx.strokeStyle = "#fff"; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(cx, cy - s); ctx.lineTo(cx + s, cy); ctx.lineTo(cx, cy + s); ctx.lineTo(cx - s, cy); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#fff"; ctx.font = `800 ${Math.round(s * 1.2)}px Overpass, sans-serif`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(i.status === "crew" ? i.left : i.status === "auto" ? "•" : "!", cx, cy + 0.5);
  }
  drawTutorialTarget(now);
  drawHover();
  if (sel) { ctx.setLineDash([3, 2]); ctx.lineWidth = 1.6; ctx.strokeStyle = COL.hivis; ctx.strokeRect(sel.x * TS + 0.8, sel.y * TS + 0.8, TS - 1.6, TS - 1.6); ctx.setLineDash([]); }
  // district labels
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  for (const d of DISTRICTS) {
    const size = d.size * clamp(1.2 / z, 0.7, 1.6);
    ctx.font = `${d.water ? "italic 600" : "800"} ${size}px Overpass, sans-serif`;
    try { ctx.letterSpacing = `${size * 0.18}px`; } catch (e) {}
    ctx.lineWidth = 3; ctx.strokeStyle = d.water ? "rgba(134,177,196,.8)" : "rgba(230,234,225,.85)"; ctx.strokeText(d.name, d.x * TS, d.y * TS);
    ctx.fillStyle = d.water ? "rgba(30,60,80,.75)" : "rgba(30,43,56,.7)"; ctx.fillText(d.name, d.x * TS, d.y * TS);
  }
  try { ctx.letterSpacing = "0px"; } catch (e) {}
  // screen-space
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  if (S.snow > 0) { ctx.fillStyle = S.plowed ? "rgba(255,255,255,.12)" : "rgba(255,255,255,.3)"; ctx.fillRect(0, 0, viewW, viewH); }
  if (flashMsg && now < flashMsg.until) {
    ctx.font = "800 13px Overpass, sans-serif"; const w = ctx.measureText(flashMsg.msg).width + 22;
    ctx.fillStyle = COL.bad; ctx.fillRect(viewW / 2 - w / 2, 10, w, 26); ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(flashMsg.msg, viewW / 2, 24);
  }
}
function drawHover() {
  if (!hover) return;
  const { x, y } = hover;
  let ok, label, rect;
  if (tool === "place" && placing) {
    const site = siteAt(x, y); [ok, label] = checkSite(x, y); rect = site;
    ctx.fillStyle = ok ? "rgba(47,125,79,.25)" : "rgba(191,58,43,.25)"; ctx.fillRect(site.x * TS, site.y * TS, site.w * TS, site.h * TS);
    if (PROJ[placing.type].rpz) drawRPZ(ctx, { type: placing.type, ...site });
    if (ok) label = money(label);
  } else {
    const r = RADIUS[tool];
    if (r) { ctx.fillStyle = "rgba(232,89,12,.08)"; ctx.beginPath();
      for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) if (Math.abs(dx) + Math.abs(dy) <= r && inb(x + dx, y + dy)) ctx.rect((x + dx) * TS, (y + dy) * TS, TS, TS);
      ctx.fill(); }
    rect = { x, y, w: 1, h: 1 };
    if (TOOL[tool] && TOOL[tool].proj) return;
    [ok, label] = check(tool, x, y);
    if (ok) label = label === "dispatch" ? "Dispatch crew" : label === "landmark" ? "Demolish landmark" : money(label);
  }
  ctx.lineWidth = 1.6; ctx.strokeStyle = tool === "inspect" ? COL.ink : ok ? COL.good : COL.bad;
  ctx.strokeRect(rect.x * TS + 0.8, rect.y * TS + 0.8, rect.w * TS - 1.6, rect.h * TS - 1.6);
  if (tool === "inspect" || !label) return;
  const z = cam.z, fs = 11 / z;
  ctx.font = `600 ${fs}px 'Overpass Mono', monospace`; const w = ctx.measureText(label).width + 10 / z, hh = 16 / z;
  let lx = (rect.x + rect.w) * TS + 4 / z, ly = rect.y * TS - hh - 2 / z;
  if (lx + w > cam.x + viewW / z) lx = rect.x * TS - w - 4 / z; if (ly < cam.y) ly = (rect.y + rect.h) * TS + 2 / z;
  ctx.fillStyle = ok ? COL.ink : COL.bad; ctx.fillRect(lx, ly, w, hh); ctx.fillStyle = "#fff"; ctx.textAlign = "left"; ctx.textBaseline = "middle"; ctx.fillText(label, lx + 5 / z, ly + hh / 2 + 0.5 / z);
}

// ── minimap ──────────────────────────────────────────────────────────────────
function drawMinimap() {
  const m = $("minimap"); if (!m) return; const c = m.getContext("2d"), s = m.width / W;
  const tc = [COL.grass, COL.sea, COL.fresh, COL.forest, COL.hill, COL.marsh, COL.beach];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const t = T_(x, y);
    c.fillStyle = isRoad(t) ? (t.b === "hwy" ? "#1E2B38" : "#555") : isZone(t) ? (t.lvl ? COL[t.b + "b"] : COL[t.b]) : t.b === "proj" ? "#6E9B5A" : t.b ? "#E8590C" : tc[t.ter];
    c.fillRect(x * s, y * s, s, s);
  }
  for (const i of S.inc) if (i.status === "open") { c.fillStyle = COL.hivis; c.fillRect(i.x * s - 2, i.y * s - 2, 5, 5); }
  c.strokeStyle = COL.ink; c.lineWidth = 1.5; c.strokeRect(cam.x / TS * s, cam.y / TS * s, viewW / cam.z / TS * s, viewH / cam.z / TS * s);
}
