"use strict";
// ─── Right-of-Way · simulation ──────────────────────────────────────────────

const monthOf = d => Math.floor(d / 30) % 12;
function dateStr(d) { return `${MONTHS[monthOf(d)]} ${String(d % 30 + 1).padStart(2, "0")}, ${START_YEAR + Math.floor(d / 360)}`; }
function resetLedger() { S.ledger = { maint: 0, emergency: 0, fines: 0, water: 0, snow: 0 }; }
function log(text, cls = "") { S.news.unshift({ d: S.day, text, cls }); if (S.news.length > 80) S.news.pop(); if (typeof renderNews === "function") renderNews(); }
function grace() { return S.tut.on && S.day < 360; }
const proj = id => S.projects.find(p => p.id === id);
function unlocked(id) {
  const tl = TOOL[id]; if (!tl.unlock) return true;
  S.unlocked = S.unlocked || {};
  if (S.unlocked[id]) return true;
  if (S.pop >= tl.unlock) { S.unlocked[id] = true; return true; }
  return false;
}
function street(x, y) { const L = n => String.fromCharCode(65 + n); return `${x < 26 ? L(x) : x < 52 ? "A" + L(x - 26) : x < 78 ? "B" + L(x - 52) : "C" + L(x - 78)}-${y + 1}`; }

function computeAll() { computeNetworks(); computeTraffic(); computeValue(); computeStats(); }

// ── utility networks ─────────────────────────────────────────────────────────
function passable(t, m) {
  if (!isRoad(t) || t.sink) return false;
  if (m === "power" && t.fP) return false;
  if (m === "water" && t.fW) return false;
  return true;
}
const summer = () => { const m = monthOf(S.day); return m >= 5 && m <= 8; };
function demandOf(t, m) {
  const z = ZONE[t.b]; if (!z || !t.lvl) return 0;
  const p = z.pop[t.lvl], j = z.jobs[t.lvl];
  if (m === "power") return (p * 0.04 + j * 0.05) * (S.heat > 0 ? 1.3 : 1);
  if (m === "water") return (p * 150 + j * 50) / 1e6;
  return (p * 150 + j * 50) * 0.9 / 1e6;
}
function projDemand(p, m) {
  if (p.status !== "open") return 0;
  const d = PROJ[p.type], a = ARCH_BY[p.arch] || ARCH[0];
  if (m === "power") return d.power * a.power;
  let w = d.water;
  if (p.golf) w *= GOLF_BY[p.golf].water * (summer() ? 1.6 : 0.6);
  return m === "water" ? w : d.water * 0.5;
}
function perimeter(p) {
  const out = [];
  for (let x = p.x; x < p.x + p.w; x++) { out.push([x, p.y - 1], [x, p.y + p.h]); }
  for (let y = p.y; y < p.y + p.h; y++) { out.push([p.x - 1, y], [p.x + p.w, y]); }
  return out.filter(([x, y]) => inb(x, y));
}
function computeNetworks() {
  S.net = {};
  const facs = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const t = T_(x, y); if (t.b === "power" || t.b === "pump" || t.b === "sewage") facs.push([t, x, y]); }
  for (const [m, plant, flag] of [["power", "power", "pw"], ["water", "pump", "wt"], ["sewer", "sewage", "sw"]]) {
    const comp = new Int32Array(W * H).fill(-1), comps = [];
    for (let i = 0; i < W * H; i++) {
      if (comp[i] >= 0 || !passable(S.tiles[i], m)) continue;
      const c = comps.length; comps.push({ supply: 0, demand: 0 });
      const q = [i]; comp[i] = c;
      while (q.length) { const k = q.pop(), x = k % W, y = (k / W) | 0;
        for (const [dx, dy] of N4) { const nx = x + dx, ny = y + dy; if (!inb(nx, ny)) continue; const j = idx(nx, ny);
          if (comp[j] < 0 && passable(S.tiles[j], m)) { comp[j] = c; q.push(j); } } }
    }
    const adj = (x, y) => { for (const [dx, dy] of N4) { const nx = x + dx, ny = y + dy; if (inb(nx, ny) && comp[idx(nx, ny)] >= 0) return comp[idx(nx, ny)]; } return -1; };
    let supply = 0, demand = 0, served = 0;
    for (const [t, x, y] of facs) {
      if (t.b !== plant) continue;
      const c = adj(x, y); t.link = c >= 0;
      if (plant === "pump" && !N4.some(([dx, dy]) => inb(x + dx, y + dy) && T_(x + dx, y + dy).ter === FRESH)) { t.salt = true; continue; }
      t.salt = false;
      if (c >= 0 && !t.off) { comps[c].supply += CAP[plant]; supply += CAP[plant]; }
    }
    const users = [];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const t = T_(x, y); if (!isZone(t)) continue;
      const c = adj(x, y); users.push([t, c, x, y, demandOf(t, m)]);
    }
    for (const p of S.projects) {
      let c = -1; for (const [x, y] of perimeter(p)) { if (comp[idx(x, y)] >= 0) { c = comp[idx(x, y)]; if (comps[c].supply > 0) break; } }
      users.push([p, c, p.x, p.y, projDemand(p, m)]);
    }
    for (const u of users) if (u[1] >= 0) { comps[u[1]].demand += u[4]; demand += u[4]; }
    for (const [t, c, x, y, d] of users) {
      if (c < 0) { t[flag] = false; continue; }
      const k = comps[c], ratio = k.demand > 0 ? Math.min(1, k.supply / k.demand) : (k.supply > 0 ? 1 : 0);
      t[flag] = k.supply > 0 && hash(x, y) < ratio + 0.0001;
      if (t[flag]) served += d;
    }
    for (let i = 0; i < W * H; i++) { const t = S.tiles[i]; if (!isRoad(t)) continue; const c = comp[i];
      t["r_" + m] = c < 0 ? -1 : (comps[c].supply <= 0 ? 0 : Math.min(1, comps[c].demand > 0 ? comps[c].supply / comps[c].demand : 1)); }
    S.net[m] = { supply, demand, served: demand > 0 ? served / demand : 1 };
  }
}

// ── traffic: gravity model + congested (BPR) shortest paths ──────────────────
function effCap(t) { return ROAD[t.b].cap * (t.ix ? CTL_FACTOR[t.ctl || "none"] : 1) * (S.snow > 0 && !S.plowed ? 0.6 : 1); }
const vcOf = t => isRoad(t) ? t.load / effCap(t) : 0;
function los(vc) { return vc < 0.6 ? "A" : vc < 0.7 ? "B" : vc < 0.8 ? "C" : vc < 0.9 ? "D" : vc < 1 ? "E" : "F"; }
function canMove(a, b) {
  if (!isOpen(a) || !isOpen(b)) return false;
  const ha = a.b === "hwy", hb = b.b === "hwy";
  if (ha === hb) return true;
  return (ha ? b : a).b === "ramp";
}
function accessTile(x, y) { for (const [dx, dy] of N4) { const nx = x + dx, ny = y + dy; if (inb(nx, ny)) { const r = T_(nx, ny); if (isLocal(r) && isOpen(r)) return idx(nx, ny); } } return -1; }

class Heap {
  constructor() { this.k = []; this.v = []; }
  push(key, val) { const k = this.k, v = this.v; let i = k.length; k.push(key); v.push(val);
    while (i > 0) { const p = (i - 1) >> 1; if (k[p] <= key) break; k[i] = k[p]; v[i] = v[p]; i = p; } k[i] = key; v[i] = val; }
  pop() { const k = this.k, v = this.v, top = v[0], lk = k.pop(), lv = v.pop(); const n = k.length;
    if (n) { let i = 0; for (;;) { let c = 2 * i + 1; if (c >= n) break; if (c + 1 < n && k[c + 1] < k[c]) c++; if (k[c] >= lk) break; k[i] = k[c]; v[i] = v[c]; i = c; } k[i] = lk; v[i] = lv; }
    return top; }
  get size() { return this.k.length; }
}
function computeTraffic() {
  const N = W * H, tiles = S.tiles;
  const cost = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    const t = tiles[i]; if (!isRoad(t)) continue;
    if (isLocal(t)) { const x = i % W, y = (i / W) | 0; let n = 0; for (const [dx, dy] of N4) if (inb(x + dx, y + dy) && isLocal(T_(x + dx, y + dy))) n++; t.ix = n >= 3 && t.st !== "bridge"; } else t.ix = false;
    if (!isOpen(t)) { cost[i] = -1; continue; }
    const vc = Math.min(3, t.load / effCap(t));
    let c = ROAD[t.b].time * (1 + 0.15 * vc ** 4);
    if (t.ix) c += t.ctl === "round" ? 0.15 : t.ctl === "signal" ? 0.3 : 0.5 * (1 + Math.min(vc, 2));
    if (S.snow > 0) c *= S.plowed ? 1.15 : 1.6;
    cost[i] = c;
  }
  // destinations: job sites clustered into districts, plus the region beyond the map edge
  const buckets = new Map();
  const addSeed = (key, w, seed) => { if (seed < 0) return; let b = buckets.get(key); if (!b) buckets.set(key, b = { w: 0, seeds: new Set() }); b.w += w; b.seeds.add(seed); };
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const t = T_(x, y);
    if ((t.b === "C" || t.b === "I") && t.lvl) addSeed(((x >> 4) << 8) | (y >> 4), ZONE[t.b].jobs[t.lvl], accessTile(x, y));
    if (isOpen(t) && (x === 0 || y === 0 || x === W - 1 || y === H - 1)) addSeed(-1, 0, idx(x, y));
  }
  for (const p of S.projects) if (p.status === "open") {
    const wgt = PROJ[p.type].jobs + (p.type === "airport" ? (S.pop || 0) * 0.12 : p.type === "airfield" ? (S.pop || 0) * 0.04 : 0);
    for (const [x, y] of perimeter(p)) { const t = T_(x, y); if (isLocal(t) && isOpen(t)) addSeed(1e6 + p.id, wgt, idx(x, y)); }
    const b = buckets.get(1e6 + p.id); if (b) b.w = wgt;
  }
  const edge = buckets.get(-1); if (edge) edge.w = (S.pop || 0) * 0.25 + 40;
  const centers = [...buckets.entries()].filter(([k, b]) => b.w > 0 && b.seeds.size).sort((a, b) => b[1].w - a[1].w).slice(0, 8).map(e => e[1]);
  if (edge && edge.seeds.size && !centers.includes(edge)) centers.push(edge);
  S.region = !!(edge && edge.seeds.size);
  S.regionHwy = [...(edge ? edge.seeds : [])].some(i => tiles[i].b === "hwy");
  const trees = centers.map(cn => {
    const dist = new Float32Array(N).fill(Infinity), par = new Int32Array(N).fill(-1), h = new Heap();
    for (const s of cn.seeds) { if (cost[s] < 0) continue; dist[s] = cost[s]; h.push(cost[s], s); }
    while (h.size) {
      const i = h.pop(), d = dist[i], x = i % W, y = (i / W) | 0;
      for (const [dx, dy] of N4) { const nx = x + dx, ny = y + dy; if (!inb(nx, ny)) continue; const j = idx(nx, ny);
        if (cost[j] < 0 || !canMove(tiles[i], tiles[j])) continue;
        const nd = d + cost[j]; if (nd < dist[j]) { dist[j] = nd; par[j] = i; h.push(nd, j); } }
    }
    return { w: cn.w, dist, par };
  });
  for (const t of tiles) t.load = 0;
  let tripSum = 0, tripDist = 0, stranded = 0;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const t = T_(x, y); if (!isZone(t) || !t.lvl) continue;
    const a = accessTile(x, y); if (a < 0) continue;
    if (t.b !== "R") { tiles[a].load += ZONE[t.b].jobs[t.lvl] * 0.15; continue; }
    const trips = ZONE.R.pop[t.lvl] * 0.4;
    let wsum = 0; const ws = trees.map(tr => { const d = tr.dist[a]; const w = isFinite(d) ? tr.w / (1 + d) ** 1.5 : 0; wsum += w; return w; });
    if (wsum <= 0) { stranded += trips; continue; }
    trees.forEach((tr, k) => {
      if (!ws[k]) return; const share = trips * ws[k] / wsum;
      tripSum += share; tripDist += share * tr.dist[a];
      let i = a, steps = 0; while (i >= 0 && steps++ < 600) { tiles[i].load += share; i = tr.par[i]; }
    });
  }
  S.commute = tripSum ? 8 + tripDist / tripSum * 1.6 : 0;
  S.stranded = stranded;
}

// ── land value ───────────────────────────────────────────────────────────────
function computeValue() {
  const N = W * H, v = new Float32Array(N).fill(1);
  const stamp = (x, y, r, amt) => { for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { const nx = x + dx, ny = y + dy; if (!inb(nx, ny)) continue;
    const d = Math.hypot(dx, dy); if (d > r) continue; v[idx(nx, ny)] += amt * (1 - d / (r + 1)); } };
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const t = T_(x, y);
    if (t.b === "park") stamp(x, y, RADIUS.park, 0.35);
    else if (t.b === "I" && t.lvl) stamp(x, y, 3, -0.1);
    else if (t.b === "hwy") stamp(x, y, 1, -0.12);
    else if (t.b === "power" || t.b === "sewage") stamp(x, y, 3, -0.2);
    if (t.ter === HILL) v[idx(x, y)] += 0.15;
    if (t.ter === SEA && (x + y) % 2 === 0) stamp(x, y, 2, 0.06);
  }
  for (const p of S.projects) {
    if (p.status !== "open") continue;
    const cx = p.x + p.w / 2, cy = p.y + p.h / 2;
    if (p.golf) stamp(Math.round(cx), Math.round(cy), Math.round(Math.max(p.w, p.h) / 2 + 6), 0.9 * GOLF_BY[p.golf].prestige);
    if (p.type === "hall") stamp(Math.round(cx), Math.round(cy), 6, 0.3 * ARCH_BY[p.arch].prestige);
    if (PROJ[p.type].noise) stamp(Math.round(cx), Math.round(cy), PROJ[p.type].noise + Math.round(p.w / 2), -0.7);
  }
  S.tiles.forEach((t, i) => t.val = clamp(v[i], 0.3, 2.8));
}
function markRPZ() {
  for (const t of S.tiles) t.rpz = false;
  for (const p of S.projects) for (const [x, y] of rpzTiles(p)) T_(x, y).rpz = true;
}
function rpzTiles(p) {
  const d = PROJ[p.type]; if (!d.rpz) return [];
  const out = [], horiz = p.w >= p.h, mid = horiz ? p.y + Math.floor(p.h / 2) : p.x + Math.floor(p.w / 2);
  for (let k = 1; k <= d.rpz; k++) for (let s = -Math.ceil(k / 2); s <= Math.ceil(k / 2); s++) {
    const pts = horiz ? [[p.x - k, mid + s], [p.x + p.w - 1 + k, mid + s]] : [[mid + s, p.y - k], [mid + s, p.y + p.h - 1 + k]];
    for (const [x, y] of pts) if (inb(x, y)) out.push([x, y]);
  }
  return out;
}

// ── stats & report card ──────────────────────────────────────────────────────
function inRadius(x, y, type, r) {
  for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
    if (Math.abs(dx) + Math.abs(dy) > r) continue; const nx = x + dx, ny = y + dy;
    if (inb(nx, ny)) { const t = T_(nx, ny); if (t.b === type && !t.off) return true; }
  }
  return false;
}
function riverside(x, y, ter) { for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const nx = x + dx, ny = y + dy; if (inb(nx, ny) && (ter ? T_(nx, ny).ter === ter : isWater(T_(nx, ny).ter)) && !isRoad(T_(nx, ny))) return true; } return false; }
function leveed(x, y) { for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const nx = x + dx, ny = y + dy; if (inb(nx, ny) && T_(nx, ny).b === "levee") return true; } return false; }
function computeStats() {
  let pop = 0, jobs = 0, cJobs = 0, iJobs = 0, parks = 0;
  let rc = 0, rcond = 0, rcong = 0, bc = 0, bcond = 0, bclosed = 0, tn = 0, near = 0, prot = 0, vcs = 0;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const t = T_(x, y);
    if (isZone(t)) { pop += ZONE[t.b].pop[t.lvl]; const j = ZONE[t.b].jobs[t.lvl]; jobs += j; if (t.b === "C") cJobs += j; if (t.b === "I") iJobs += j;
      if (t.lvl && riverside(x, y)) { near++; if (leveed(x, y)) prot++; } }
    if (t.b === "park") parks++;
    if (isRoad(t)) {
      if (t.st === "bridge") { bc++; bcond += t.cond; if (t.closed) bclosed++; }
      else if (t.st === "tunnel") tn++;
      else { rc++; rcond += t.cond; vcs += Math.min(1.5, vcOf(t)); if (vcOf(t) >= 0.9) rcong++; }
    }
  }
  let projApproval = 0, projJobs = 0;
  for (const p of S.projects) if (p.status === "open") { projJobs += PROJ[p.type].jobs; if (p.type === "hall") projApproval += PROJ.hall.approval + ARCH_BY[p.arch].approval; else projApproval += ARCH_BY[p.arch].approval * 0.5; }
  jobs += projJobs; cJobs += projJobs;
  Object.assign(S, { pop, jobs, cJobs, iJobs });
  const tr = S.tax - 9, reg = (S.region ? 0.08 : -0.1) + (S.regionHwy ? 0.12 : 0);
  const air = S.projects.some(p => p.status === "open" && PROJ[p.type].rpz) ? 0.12 : 0;
  S.demand = {
    R: clamp((jobs * 1.15 + 70 - pop) / Math.max(60, pop * 0.25) - tr * 0.06 + reg, -1, 1),
    C: clamp((pop * 0.35 + 15 - cJobs) / Math.max(30, pop * 0.12) - tr * 0.06 + air, -1, 1),
    I: clamp((pop * 0.45 + 25 - iJobs) / Math.max(30, pop * 0.15) - tr * 0.06 + reg + air, -1, 1),
  };
  const open = S.inc.filter(i => i.status !== "done");
  const out = (1 - S.net.power.served) + (1 - S.net.water.served);
  const avgCond = rc ? rcond / rc : 100, congPct = rc ? rcong / rc : 0;
  const overflow = S.net.sewer.demand > S.net.sewer.supply && pop > 150;
  let h = 72 - tr * 3 - out * 35 - congPct * 25 - Math.max(0, 60 - avgCond) * 0.4 - open.length * 2 - (overflow ? 10 : 0)
        + Math.min(10, parks * 60 / Math.max(1, pop / 10)) + projApproval - (S.snow > 0 ? (S.plowed ? 2 : 14) : 0) - Math.max(0, S.commute - 30) * 0.5;
  S.happy = clamp(S.happy * 0.8 + clamp(h, 0, 100) * 0.2, 0, 100);
  S.overflow = overflow;
  const margin = n => n.demand <= 0 ? 100 : clamp((n.supply / n.demand - 1) / 0.25, 0, 1) * 100;
  const count = k => open.filter(i => i.kind === k).length;
  S.grades = [
    ["Roads", `PCI ${avgCond.toFixed(0)} · ${(congPct * 100).toFixed(0)}% of streets at LOS E–F`, avgCond * 0.75 + (1 - congPct) * 25 - count("sink") * 8],
    ["Bridges & tunnels", bc || tn ? `${bc} bridge spans, avg NBI ${nbi(bc ? bcond / bc : 100)} · ${bclosed} closed${tn ? ` · ${tn} tunnel tiles` : ""}` : "None yet", bc || tn ? (bc ? bcond / bc : 95) - bclosed * 20 + 8 - count("tunnel") * 15 : null],
    ["Transportation", `Avg commute ${S.commute.toFixed(0)} min${S.regionHwy ? " · on the interstate" : S.region ? " · state road link" : " · no regional link"}`, clamp(100 - Math.max(0, S.commute - 18) * 2.5 - congPct * 40 + (S.regionHwy ? 5 : 0) - count("crash") * 3, 0, 100)],
    ["Drinking water", `${S.net.water.supply.toFixed(2)} of ${S.net.water.demand.toFixed(2)} MGD · ${count("main")} breaks`, S.net.water.served * 70 + margin(S.net.water) * 0.3 - count("main") * 8 - count("pump") * 10],
    ["Energy", `${S.net.power.supply.toFixed(0)} of ${S.net.power.demand.toFixed(0)} MW`, S.net.power.served * 70 + margin(S.net.power) * 0.3 - count("lines") * 5 - count("plant") * 10],
    ["Wastewater", `${S.net.sewer.supply.toFixed(2)} of ${S.net.sewer.demand.toFixed(2)} MGD${overflow ? " · overflowing" : ""}`, S.net.sewer.served * 70 + margin(S.net.sewer) * 0.3],
    ["Flood protection", near ? `${prot} of ${near} waterfront blocks behind levees` : "No waterfront development", near ? prot / near * 100 : null],
  ];
}
const letter = s => s == null ? "NA" : s >= 90 ? "A" : s >= 80 ? "B" : s >= 70 ? "C" : s >= 60 ? "D" : "F";
function pciLabel(c) { return c >= 85 ? "Good" : c >= 70 ? "Satisfactory" : c >= 55 ? "Fair" : c >= 40 ? "Poor" : c >= 25 ? "Very poor" : c >= 10 ? "Serious" : "Failed"; }
const nbi = c => Math.max(0, Math.min(9, Math.round(c / 100 * 9)));

// ── incidents ────────────────────────────────────────────────────────────────
function addInc(kind, x, y, quiet) {
  const ex = S.inc.find(i => i.status !== "done" && i.kind === kind && i.x === x && i.y === y); if (ex) return ex;
  const inc = { id: S.nextId++, kind, x, y, start: S.day, status: INC[kind].auto ? "auto" : "open", left: INC[kind].auto ? 2 : 0 };
  S.inc.push(inc);
  if (!quiet) log(`${INC[kind].name} at ${street(x, y)}.`, kind === "crash" ? "" : "bad");
  return inc;
}
function crews() { let n = 1; for (const t of S.tiles) if (t.b === "depot") n++; const busy = S.inc.filter(i => i.status === "crew" && i.kind !== "fire").length; return { total: n, free: n - busy }; }
function dispatch(id) {
  const i = S.inc.find(k => k.id === id); if (!i || i.status !== "open") return;
  const d = INC[i.kind];
  if (i.kind !== "fire" && crews().free <= 0) { flash("No crews free"); log("No crews available. Build a Works depot to add a crew.", "bad"); return; }
  if (S.funds < d.cost) { flash(`Need $${d.cost.toLocaleString()}`); return; }
  S.funds -= d.cost; S.ledger.emergency += d.cost; i.status = "crew"; i.left = d.days;
  log(i.kind === "fire" ? `Mutual aid engines en route to ${street(i.x, i.y)}.` : `Crew dispatched: ${d.name.toLowerCase()} at ${street(i.x, i.y)}. ETA ${d.days} days.`);
  if (typeof updateUI === "function") updateUI();
}
function resolve(i) {
  const t = T_(i.x, i.y); i.status = "done";
  switch (i.kind) {
    case "main": t.fW = false; t.cond = Math.min(100, t.cond + 30); break;
    case "sink": t.sink = false; t.cond = 100; break;
    case "bridge": case "tunnel": t.closed = false; t.cond = 100; break;
    case "plant": case "pump": case "flood": t.off = false; break;
    case "lines": t.fP = false; break;
    case "fire": t.fire = 0; break;
  }
  if (!INC[i.kind].auto) log(`${INC[i.kind].name} at ${street(i.x, i.y)} resolved.`, "good");
}
function clearInc(x, y, kind) { S.inc.forEach(i => { if (i.status !== "done" && i.x === x && i.y === y && (!kind || i.kind === kind)) i.status = "done"; }); }
function rollIncidents() {
  const rnd = Math.random, g = grace();
  const plantLoad = S.net.power.supply ? S.net.power.demand / S.net.power.supply : 0;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const t = T_(x, y);
    if (isRoad(t)) {
      if (t.st === "bridge" && !t.closed && t.cond < 30) { t.closed = true; addInc("bridge", x, y); }
      if (t.st === "bridge" && t.cond <= 3) { collapse(x, y); continue; }
      if (g) continue;
      if (!t.st && !t.fW && !t.sink && t.r_water > 0 && t.cond < 65 && rnd() < 0.0007 * (65 - t.cond) / 65) { t.fW = true; addInc("main", x, y); }
      if (!t.st && !t.sink && t.cond < 20 && rnd() < 0.003) { t.sink = true; t.fW = false; clearInc(x, y, "main"); addInc("sink", x, y); }
      if (t.st === "tunnel" && !t.closed && rnd() < 0.0004) { t.closed = true; addInc("tunnel", x, y); }
      if (t.ix && t.load > 20) { const vc = vcOf(t); const base = 0.004 * vc * (t.ctl === "round" ? 0.15 : t.ctl === "signal" ? 0.35 : 1) * (S.snow > 0 ? 3 : 1);
        if (vc > 0.75 && rnd() < base && !S.inc.some(i => i.kind === "crash" && i.status !== "done" && i.x === x && i.y === y)) addInc("crash", x, y); }
      continue;
    }
    if (g) continue;
    if (t.b === "power" && !t.off && t.link && rnd() < 0.0012 + (plantLoad > 0.9 ? 0.01 : 0)) { t.off = true; addInc("plant", x, y); }
    if (t.b === "pump" && !t.off && t.link && rnd() < 0.001) { t.off = true; addInc("pump", x, y); }
    if (isZone(t) && t.lvl && !t.fire && rnd() < 0.00012 * (t.b === "I" ? 2.5 : 1) * (S.heat > 0 ? 1.6 : 1)) { t.fire = 1; log(`Fire reported at ${street(x, y)}.`, "bad"); }
  }
}
function collapse(x, y) {
  const t = T_(x, y); clearInc(x, y);
  clearTile(t);
  S.funds -= 4000; S.ledger.fines += 4000; S.happy = Math.max(0, S.happy - 15);
  log(`A bridge span at ${street(x, y)} collapsed. $4,000 liability settlement. The crossing must be rebuilt.`, "bad");
}
function floodTile(x, y) {
  const t = T_(x, y); if (isWater(t.ter) || t.b === "levee" || leveed(x, y)) return 0;
  t.flood = 6;
  let hit = 0;
  if (isZone(t) && t.lvl) { t.lvl--; hit = 1; }
  if (isRoad(t) && !t.st) t.cond = Math.max(0, t.cond - 30);
  if ((t.b === "pump" || t.b === "sewage" || t.b === "power") && !t.off) { t.off = true; addInc("flood", x, y); }
  return hit;
}
function linesDown(n) {
  const roads = []; S.tiles.forEach((t, i) => { if (isRoad(t) && !t.st && t.r_power > 0 && !t.fP) roads.push(i); });
  for (let k = 0; k < n && roads.length; k++) { const i = roads.splice(Math.floor(Math.random() * roads.length), 1)[0]; S.tiles[i].fP = true; addInc("lines", i % W, (i / W) | 0, true); }
  if (n) log("Power lines down. Check Work Orders.", "bad");
}
function weather() {
  const m = monthOf(S.day), rnd = Math.random;
  if (S.day % 30 === 1 && m === 1) log("Pothole season: freeze-thaw cycles through April will wear pavement almost twice as fast.");
  if (grace()) return;
  if ((m <= 2 || m === 11) && S.snow <= 0 && rnd() < 0.008) {
    const inches = Math.round(8 + rnd() * 18), roads = S.tiles.filter(isRoad).length;
    if (S.snowBudget) { const c = roads * 3; S.funds -= c; S.ledger.snow += c; S.snow = 2; S.plowed = true; log(`Nor'easter drops ${inches} inches of snow. Plows and salt trucks are out ($${c.toLocaleString()}).`, "bad"); }
    else { S.snow = 7; S.plowed = false; log(`Nor'easter drops ${inches} inches of snow. With no snow budget, streets stay buried for a week.`, "bad"); }
    let hit = 0; for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (riverside(x, y, SEA) && rnd() < 0.25) hit += floodTile(x, y);
    if (hit) log(`Coastal flooding damaged ${hit} waterfront buildings.`, "bad");
  }
  if (m >= 5 && m <= 7 && S.heat <= 0 && rnd() < 0.012) { S.heat = 10; log("Heat wave: power demand up 30% for 10 days. Watch plant load.", "bad"); }
  if (m >= 2 && m <= 4 && rnd() < 0.004) {
    const x0 = Math.floor(rnd() * 40); let hit = 0;
    log("Spring rains: the Quill and Iron rivers are over their banks.", "bad");
    for (let y = 0; y < H; y++) for (let x = x0; x < x0 + 30 && x < W; x++) if (riverside(x, y, FRESH)) hit += floodTile(x, y);
    if (hit) log(`River flooding damaged ${hit} unprotected buildings. Levees would have held.`, "bad");
  }
  if (m >= 7 && m <= 9 && rnd() < 0.003) {
    let hit = 0; log("Hurricane making landfall. Storm surge in the harbor and along the South Shore.", "bad");
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const t = T_(x, y); if (riverside(x, y, SEA) || (t.ter === MARSH && rnd() < 0.5)) hit += floodTile(x, y); }
    if (hit) log(`Storm surge damaged ${hit} unprotected buildings.`, "bad");
    linesDown(3 + Math.floor(rnd() * 4));
  }
}
function progressIncidents() {
  for (const i of S.inc) {
    if (i.status === "crew" || i.status === "auto") { if (--i.left <= 0) resolve(i); continue; }
    if (i.status !== "open") continue;
    const age = S.day - i.start, t = T_(i.x, i.y);
    if (i.kind === "main") { S.funds -= 25; S.ledger.water += 25;
      if (age > 25) { i.status = "done"; t.fW = false; t.sink = true; addInc("sink", i.x, i.y, true); log(`The unrepaired main at ${street(i.x, i.y)} washed out the road base. It's a sinkhole now.`, "bad"); } }
    if (i.kind === "bridge") t.cond = Math.max(0, t.cond - 0.25);
  }
  S.inc = S.inc.filter(i => i.status !== "done" || S.day - i.start < 200);
}
function fires() {
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const t = T_(x, y); if (!t.fire) continue;
    t.fire++;
    if (inRadius(x, y, "fire", RADIUS.fire)) { if (t.fire > 2) { t.fire = 0; if (t.lvl > 1) t.lvl--; log(`Fire at ${street(x, y)} knocked down by the fire department.`); } continue; }
    const i = S.inc.find(k => k.kind === "fire" && k.x === x && k.y === y && k.status !== "done") || addInc("fire", x, y, true);
    if (i.status === "crew") continue;
    if (Math.random() < 0.3) for (const [dx, dy] of N4) { const n = inb(x + dx, y + dy) && T_(x + dx, y + dy); if (n && isZone(n) && n.lvl && !n.fire && Math.random() < 0.5) n.fire = 1; }
    if (t.fire > 7) { t.fire = 0; t.lvl = 0; i.status = "done"; log(`A building at ${street(x, y)} burned down.`, "bad"); }
  }
}

// ── daily tick ───────────────────────────────────────────────────────────────
function day() {
  S.day++;
  if (S.heat > 0) S.heat--;
  if (S.snow > 0) S.snow--;
  computeNetworks();
  if (S.day % 2 === 0) computeTraffic();
  if (S.day % 10 === 0) computeValue();
  const m = monthOf(S.day), thaw = m >= 1 && m <= 3 ? 1.8 : 1;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const t = T_(x, y);
    if (t.flood) t.flood--;
    if (isRoad(t)) { const vc = Math.min(2, vcOf(t));
      const rate = t.st === "tunnel" ? 0.008 : t.st === "bridge" ? 0.03 + 0.03 * vc : (ROAD[t.b].decay + 0.05 * vc) * thaw;
      t.cond = Math.max(0, t.cond - rate); }
    if (isZone(t)) grow(t, x, y);
  }
  maintenance(); rollIncidents(); weather(); progressIncidents(); fires(); buildProjects();
  computeStats();
  milestones();
  if (S.day % 30 === 0) month();
}
function grow(t, x, y) {
  if (t.fire) return;
  const ok = accessTile(x, y) >= 0 && t.pw && t.wt;
  if (t.lvl && !ok) { if (++t.bad > 40 && Math.random() < 0.15) { t.bad = 20; t.lvl--; if (Math.random() < .3) log(`A ${t.b === "R" ? "household" : "business"} at ${street(x, y)} moved out after losing service.`); } return; }
  t.bad = Math.max(0, t.bad - 1);
  if (!ok || S.snow > 0 || Math.random() > 0.035 * (S.happy / 65)) return;
  let score = S.demand[t.b] * 60 + S.happy * 0.45 + (t.val - 1) * 25;
  let cong = 0; for (const [dx, dy] of N4) { const n = inb(x + dx, y + dy) && T_(x + dx, y + dy); if (isRoad(n)) cong = Math.max(cong, vcOf(n)); }
  if (cong > 1) score -= 20;
  if (t.flood) score -= 30;
  const need = [25, 35, 48][t.lvl] ?? 999;
  if (t.lvl === 2 && !t.sw) return;
  if (t.rpz && t.lvl >= 1) return;
  if (score > need && t.lvl < 3) t.lvl++;
  else if (score < 5 && t.lvl > 0 && Math.random() < 0.3) t.lvl--;
}
function maintenance() {
  if (S.funds <= 0) return;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    if (T_(x, y).b !== "depot") continue;
    const cand = [];
    for (let dy = -RADIUS.depot; dy <= RADIUS.depot; dy++) for (let dx = -RADIUS.depot; dx <= RADIUS.depot; dx++) {
      const nx = x + dx, ny = y + dy; if (!inb(nx, ny) || Math.abs(dx) + Math.abs(dy) > RADIUS.depot) continue;
      const r = T_(nx, ny); if (isRoad(r) && r.st !== "tunnel" && r.cond < 80 && !r.closed && !r.sink) cand.push(r);
    }
    cand.sort((a, b) => a.cond - b.cond);
    for (const r of cand.slice(0, 2)) { const pts = Math.min(5, 100 - r.cond), c = pts * (r.st === "bridge" ? 10 : 2.5);
      r.cond += pts; S.funds -= c; S.ledger.maint += c; }
  }
}
function buildProjects() {
  for (const p of S.projects) {
    if (p.status !== "build") continue;
    if (++p.prog >= p.days) {
      p.status = "open";
      const d = PROJ[p.type];
      log(`${p.name} is open. Designed by ${ARCH_BY[p.arch].firm}${p.golf ? `, course by ${GOLF_BY[p.golf].firm}` : ""}.`, "good");
      computeValue(); computeNetworks();
      if (d.rpz && !S.projects.some(q => q !== p && q.status === "open" && PROJ[q.type].rpz)) log("Air service is up. Commercial and industrial demand will rise, and so will noise complaints nearby.");
    }
  }
}

// ── economy ──────────────────────────────────────────────────────────────────
function roadUpkeep() { let u = 0; for (const t of S.tiles) if (isRoad(t)) u += ROAD[t.b].upkeep + (t.st === "bridge" ? 6 : t.st === "tunnel" ? 12 : 0) + (t.ctl === "signal" ? 3 : 0); return u; }
function facilityUpkeep() { let u = 0; for (const t of S.tiles) if (UPKEEP[t.b]) u += UPKEEP[t.b]; for (const p of S.projects) if (p.status === "open") u += PROJ[p.type].upkeep * ARCH_BY[p.arch].upkeep; return Math.round(u); }
function projectIncome() {
  let tour = 0, club = 0;
  for (const p of S.projects) {
    if (p.status !== "open" || !p.pw || !p.wt) continue;
    const a = ARCH_BY[p.arch];
    if (p.type === "airfield" || p.type === "airport") {
      const landside = perimeter(p).some(([x, y]) => { for (let dy = -10; dy <= 10; dy++) for (let dx = -10; dx <= 10; dx++) { const n = inb(x + dx, y + dy) && T_(x + dx, y + dy); if (n && n.b === "ramp") return true; } return false; });
      p.landside = landside;
      tour += (p.type === "airport" ? 3000 + S.pop * 0.6 : 600 + S.pop * 0.25) * a.prestige * (landside ? 1 : 0.6);
    }
    if (p.golf) {
      const g = GOLF_BY[p.golf]; let rich = 0;
      for (let y = p.y - 12; y < p.y + p.h + 12; y++) for (let x = p.x - 12; x < p.x + p.w + 12; x++) { const t = inb(x, y) && T_(x, y); if (t && t.b === "R" && t.lvl === 3) rich++; }
      club += g.members * (PROJ[p.type].holes / 9) * (400 + rich * 25 + S.pop * 0.05) * (0.8 + a.prestige * 0.2);
    }
  }
  return { tour: Math.round(tour), club: Math.round(club) };
}
function revenue() {
  let pv = 0, jv = 0;
  for (const t of S.tiles) if (isZone(t) && t.lvl) { pv += ZONE[t.b].pop[t.lvl] * t.val; jv += ZONE[t.b].jobs[t.lvl] * t.val; }
  return { tax: Math.round(pv * S.tax * 0.22 + jv * S.tax * 0.16), fees: Math.round(S.pop * S.net.water.served * 0.35) };
}
function month() {
  const r = revenue(), pi = projectIncome(), road = roadUpkeep(), fac = facilityUpkeep();
  let debt = 0; S.bonds.forEach(b => { if (b.left > 0) { debt += 150; b.left--; } }); S.bonds = S.bonds.filter(b => b.left > 0);
  let fine = 0; if (S.overflow) { fine = 500; log("State DEP notice of violation: sewage overflowed into the harbor. $500 fine. Add wastewater capacity.", "bad"); }
  S.funds += r.tax + r.fees + pi.tour + pi.club - road - fac - debt - fine;
  const L = S.ledger;
  S.month = { label: `${MONTHS[monthOf(S.day - 1)]} ${START_YEAR + Math.floor((S.day - 1) / 360)}`, tax: r.tax, fees: r.fees, tour: pi.tour, club: pi.club, road, fac, debt,
    fine: fine + L.fines, maint: Math.round(L.maint), emergency: L.emergency, water: L.water, snow: L.snow };
  const M = S.month; M.net = M.tax + M.fees + M.tour + M.club - M.road - M.fac - M.debt - M.fine - M.maint - M.emergency - M.water - M.snow;
  resetLedger();
  S.history.push(Math.round(S.funds)); if (S.history.length > 24) S.history.shift();
  if (S.funds < 0) log("The treasury is in deficit. Raise taxes, issue a bond, or cut costs.", "bad");
  if (typeof autosave === "function") autosave();
}
function milestones() {
  while (S.milestones < MILESTONES.length && S.pop >= MILESTONES[S.milestones].pop) {
    const m = MILESTONES[S.milestones++]; S.funds += m.grant; log(`Population ${m.pop.toLocaleString()}: ${m.text}`, "good");
    if (typeof buildTools === "function") buildTools();
  }
}

// ── construction ─────────────────────────────────────────────────────────────
function terrainCost(t, base) {
  let c = base;
  if (t.ter === HILL) c *= 2;
  if (t.ter === FOREST) c += 30;
  if (t.ter === MARSH) c += 120;
  return Math.round(c);
}
const freeLot = t => !t.b || (isZone(t) && !t.lvl);
function check(id, x, y) {
  if (!inb(x, y)) return [false, ""];
  const t = T_(x, y), tl = TOOL[id];
  if (!unlocked(id)) return [false, `Unlocks at ${tl.unlock.toLocaleString()} residents`];
  const land = !isWater(t.ter);
  switch (id) {
    case "inspect": return [true, 0];
    case "road":
      if (isRoad(t)) return [false, "Already a road"];
      if (!freeLot(t)) return [false, "Occupied"];
      return [true, land ? terrainCost(t, 50) : 600];
    case "ave": if (t.b !== "road") return [false, "Pick an existing street"]; return [true, t.st === "bridge" ? 900 : 250];
    case "hwy":
      if (t.b === "hwy") return [false, "Already a highway"];
      if (!(freeLot(t) || t.b === "road" || t.b === "ave")) return [false, "Occupied"];
      if (t.st === "tunnel") return [false, "Use the tunnel tool"];
      return [true, land ? terrainCost(t, 400) : 2000];
    case "ramp":
      if (!land) return [false, "Ramps go on land"];
      if (!(freeLot(t) || t.b === "road" || t.b === "ave")) return [false, "Occupied"];
      if (!N4.some(([dx, dy]) => inb(x + dx, y + dy) && T_(x + dx, y + dy).b === "hwy")) return [false, "Must touch a highway"];
      return [true, terrainCost(t, 300)];
    case "tunnel":
      if (land) return [false, "Tunnels go under water"];
      if (t.b) return [false, "Already built"];
      return [true, 2500];
    case "signal": case "round":
      if (!isLocal(t) || t.st) return [false, "Pick a street intersection"];
      if (!t.ix) return [false, "Needs 3 or 4 streets meeting"];
      if (t.ctl === (id === "signal" ? "signal" : "round")) return [false, "Already installed"];
      return [true, TOOL[id].cost];
    case "R": case "C": case "I":
      if (!land) return [false, "Can't zone water"];
      if (t.b && !isZone(t)) return [false, "Occupied"];
      if (t.b === id) return [false, "Already zoned"];
      if (t.lvl) return [false, "Demolish the building first"];
      return [true, terrainCost(t, 20)];
    case "pump": case "sewage": case "levee":
      if (!land) return [false, "Build on the shore"];
      if (!freeLot(t)) return [false, "Occupied"];
      if (id === "pump" && !N4.some(([dx, dy]) => inb(x + dx, y + dy) && T_(x + dx, y + dy).ter === FRESH)) return [false, "Needs fresh water (river or reservoir)"];
      if (id !== "pump" && !N4.some(([dx, dy]) => inb(x + dx, y + dy) && isWater(T_(x + dx, y + dy).ter))) return [false, "Must touch the water"];
      return [true, terrainCost(t, tl.cost)];
    case "power": case "fire": case "depot": case "park":
      if (!land) return [false, "Can't build on water"];
      if (!freeLot(t)) return [false, "Occupied"];
      return [true, terrainCost(t, tl.cost)];
    case "repair": {
      if (S.inc.some(i => i.status === "open" && i.x === x && i.y === y)) return [true, "dispatch"];
      if (!isRoad(t)) return [false, "Only roads, bridges and tunnels"];
      if (t.cond >= 99) return [false, "Already in good repair"];
      return [true, Math.ceil((100 - t.cond) * (t.st === "bridge" ? 25 : 6))];
    }
    case "bulldoze":
      if (t.b === "proj") return [true, "landmark"];
      if (!t.b) return t.ter === FOREST ? [true, 30] : [false, "Nothing here"];
      return [true, 10];
  }
  return [false, ""];
}
function apply(x, y, toolId) {
  const [ok, cost] = check(toolId, x, y);
  if (toolId === "inspect") return;
  if (!ok) { if (cost) flash(cost); return; }
  if (cost === "dispatch") { dispatch(S.inc.find(i => i.status === "open" && i.x === x && i.y === y).id); return; }
  if (cost === "landmark") { confirmDemolish(T_(x, y).pid); return; }
  if (S.funds < cost) { flash(`Need $${cost.toLocaleString()}`); return; }
  const t = T_(x, y);
  S.funds -= cost;
  if (t.ter === FOREST || t.ter === MARSH) { if (toolId !== "repair" && toolId !== "signal" && toolId !== "round") { t.ter = GRASS; terrainDirty = true; } }
  switch (toolId) {
    case "repair": S.ledger.emergency += cost; t.cond = 100; log(`Resurfaced ${t.st === "bridge" ? "a bridge span" : "a road"} at ${street(x, y)} for $${cost.toLocaleString()}.`); break;
    case "bulldoze": clearInc(x, y); clearTile(t); break;
    case "ave": t.b = "ave"; break;
    case "hwy": { const st = isWater(t.ter) ? "bridge" : null; clearTile(t); Object.assign(t, { b: "hwy", st }); break; }
    case "ramp": clearTile(t); t.b = "ramp"; break;
    case "tunnel": { const hw = N4.some(([dx, dy]) => inb(x + dx, y + dy) && T_(x + dx, y + dy).b === "hwy"); clearTile(t); Object.assign(t, { b: hw ? "hwy" : "road", st: "tunnel" }); break; }
    case "signal": t.ctl = "signal"; break;
    case "round": t.ctl = "round"; break;
    case "road": { const st = isWater(t.ter) ? "bridge" : null; clearTile(t); Object.assign(t, { b: "road", st }); break; }
    default: clearTile(t); t.b = toolId;
  }
  S.counters[toolId] = (S.counters[toolId] || 0) + 1;
  computeNetworks(); computeTraffic(); computeStats();
  if (toolId === "park" || toolId === "power" || toolId === "sewage") computeValue();
}
