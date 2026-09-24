"use strict";
// ─── Right-of-Way · world state, terrain and the starting city ──────────────

let S; // the whole game state (saved)

function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const idx = (x, y) => y * W + x;
const inb = (x, y) => x >= 0 && y >= 0 && x < W && y < H;
const N4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];
const T_ = (x, y) => S.tiles[idx(x, y)];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const hash = (x, y) => (((x * 928371 + y * 123457) ^ (x * y * 7919)) >>> 0) % 997 / 997;
const isRoad = t => !!t && (t.b === "road" || t.b === "ave" || t.b === "hwy" || t.b === "ramp");
const isLocal = t => isRoad(t) && t.b !== "hwy";
const isZone = t => !!t && (t.b === "R" || t.b === "C" || t.b === "I");
const isOpen = t => isRoad(t) && !t.sink && !t.closed;
const isBridge = t => isRoad(t) && t.st === "bridge";
const isFacility = t => !!t && !!t.b && !isRoad(t) && !isZone(t) && t.b !== "proj";

function newTile(ter, e) {
  return { ter, e, b: null, lvl: 0, cond: 100, st: null, ctl: null, pid: 0, fW: false, fP: false, sink: false, closed: false, off: false, fire: 0, flood: 0, bad: 0, load: 0, val: 1, ix: false };
}
function clearTile(t) { Object.assign(t, newTile(t.ter, t.e)); }

// ── noise ────────────────────────────────────────────────────────────────────
function makeNoise(seed) {
  const h2 = (x, y) => { let n = Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(seed, 1442695041); n = Math.imul(n ^ (n >>> 13), 1274126177); n ^= n >>> 16; return (n >>> 0) / 4294967295; };
  const sm = t => t * t * (3 - 2 * t);
  const noise = (x, y) => { const xi = Math.floor(x), yi = Math.floor(y), xf = sm(x - xi), yf = sm(y - yi);
    const a = h2(xi, yi), b = h2(xi + 1, yi), c = h2(xi, yi + 1), d = h2(xi + 1, yi + 1);
    return a + (b - a) * xf + (c - a) * yf + (a - b - c + d) * xf * yf; };
  return (x, y) => (noise(x, y) * 0.5 + noise(x * 2.1, y * 2.1) * 0.25 + noise(x * 4.3, y * 4.3) * 0.125) / 0.875;
}

// ── geography ────────────────────────────────────────────────────────────────
// A composite region: a Boston-like harbor city on a peninsula, a Pittsburgh-like
// river confluence and steel heights to the west, and a Nantucket-like island offshore.
const quillY = x => 29 + 2.5 * Math.sin(x / 8) + 1.2 * Math.sin(x / 3.1);
const ironX = y => 28 - (y - quillY(28)) * 0.35 + 1.8 * Math.sin(y / 4);
const inEll = (x, y, cx, cy, rx, ry) => ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1;
function coastX(y) { if (y < 26) return 91 + 3 * Math.sin(y / 6); if (y < 52) return (y >= 34 && y <= 46) ? 86 : 95; return 87 + 3 * Math.sin(y / 4); }
const HARBOR = [77, 39, 14, 11];
const PENINSULA = [70, 37, 6.5, 5];

function terrainAt(x, y, fbm) {
  // elevation: rolling noise plus named hill masses
  const bump = (cx, cy, r, w) => w * Math.max(0, 1 - Math.hypot(x - cx, y - cy) / r);
  let e = fbm(x / 13, y / 13) * 0.5 + bump(13, 47, 17, 0.7) + bump(44, 64, 12, 0.58) + bump(26, 12, 16, 0.28) + bump(6, 20, 12, 0.3);
  let ter = GRASS;
  if (x >= coastX(y)) ter = SEA;
  if (inEll(x, y, ...HARBOR)) ter = SEA;
  if (inEll(x, y, 86, 30, 9, 5.5) && x < coastX(y)) ter = MARSH;                     // East Flats
  if (inEll(x, y, ...PENINSULA)) ter = GRASS;                                       // Old Bayford
  if (x >= 61 && x <= 66 && y >= 41 && y <= 45) ter = GRASS;                         // the Neck
  if (inEll(x, y, 101, 69, 8, 4.5)) ter = GRASS;                                     // Marrow Island
  if (x <= 66) { const q = Math.round(quillY(x)); if (y === q || y === q + 1) ter = FRESH; }
  if (y > quillY(28) + 1) { const ix = Math.round(ironX(y)); if (x === ix || x === ix + 1) ter = FRESH; }
  if (inEll(x, y, 12, 62, 6, 3.5)) ter = FRESH;                                      // Quarry Reservoir
  if (isWater(ter)) return [ter, 0];
  if (ter !== MARSH) {
    if (x >= 52 && x <= 62 && y >= 34 && y <= 40) ter = MARSH;                       // Back Marsh
    else if (e > 0.57) ter = HILL;
    else if (fbm(x / 6 + 40, y / 6) > 0.6 + (x > 50 ? 0.12 : 0) && !inEll(x, y, ...PENINSULA)) ter = FOREST;
  }
  return [ter, e];
}

function genTerrain(seed) {
  const fbm = makeNoise(seed);
  const tiles = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const [ter, e] = terrainAt(x, y, fbm); tiles.push(newTile(ter, e)); }
  // beaches on ocean-facing shores
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const t = tiles[idx(x, y)]; if (isWater(t.ter) || t.ter === MARSH) continue;
    const seaN = N4.some(([dx, dy]) => inb(x + dx, y + dy) && tiles[idx(x + dx, y + dy)].ter === SEA);
    if (seaN && !inEll(x, y, HARBOR[0], HARBOR[1], HARBOR[2] + 2, HARBOR[3] + 2) && (y > 46 || x > 95)) t.ter = BEACH;
  }
  return tiles;
}
function elevations(seed) { const fbm = makeNoise(seed), out = new Float32Array(W * H); for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) out[idx(x, y)] = terrainAt(x, y, fbm)[1]; return out; }

// ── the starting city ────────────────────────────────────────────────────────
function newGame({ guided = true, seed = 1 } = {}) {
  const rnd = mulberry32(seed * 7919 + 3);
  S = {
    v: 2, seed, day: 0, funds: guided ? 40000 : 30000, tax: 9, bonds: [], tiles: genTerrain(seed), inc: [], news: [], nextId: 1, milestones: 0,
    happy: 66, heat: 0, snow: 0, month: null, ledger: {}, projects: [], history: [], snowBudget: true,
    tut: { on: guided, step: 0, done: [], seen: {} }, counters: {}, commute: 0, cityName: CITY,
  };
  resetLedger();
  const put = (x, y, b, extra = {}) => {
    if (!inb(x, y)) return;
    const t = T_(x, y);
    if (isRoad({ b }) && isWater(t.ter)) { Object.assign(t, { b, st: "bridge", cond: 100 }, extra); return; }
    if (isWater(t.ter)) return;
    if (t.ter === FOREST) t.ter = GRASS;
    Object.assign(t, { b, st: null }, extra);
  };
  // wandering colonial streets: step toward each waypoint, with the odd jog
  const path = (pts, b = "road", extra = {}) => {
    let [x, y] = pts[0]; put(x, y, b, extra);
    for (const [tx, ty] of pts.slice(1)) {
      let guard = 0;
      while ((x !== tx || y !== ty) && guard++ < 200) {
        const dx = tx - x, dy = ty - y;
        let alongX = Math.abs(dx) >= Math.abs(dy); if (dx && dy && rnd() < 0.22) alongX = !alongX;
        if (alongX) x += Math.sign(dx); else y += Math.sign(dy);
        put(x, y, b, extra);
      }
    }
  };
  // Old Bayford
  path([[62, 43], [65, 41], [68, 38], [71, 35], [74, 36]]);
  path([[64, 38], [70, 38], [75, 37]]);
  path([[67, 34], [72, 34]]);
  path([[66, 41], [71, 40]]);
  path([[69, 33], [69, 35]]); path([[72, 36], [73, 40]]);
  // mainland: Route 9 from the west edge, River St up to the water plant, Northbank over the old bridge
  for (let x = 0; x <= 62; x++) put(x, 44, "road", { cond: 70 + rnd() * 20 });
  for (let y = 34; y <= 44; y++) put(61, y, "road");
  for (let y = 24; y <= 33; y++) put(70, y, "road");
  for (let x = 66; x <= 74; x++) put(x, 24, "road");
  put(60, 34, "pump"); put(59, 45, "power");
  // zoning: everything fronting a street on the peninsula
  for (let y = 30; y <= 46; y++) for (let x = 60; x <= 78; x++) {
    const t = T_(x, y); if (t.b || isWater(t.ter) || !inEll(x, y, ...PENINSULA)) continue;
    if (!N4.some(([dx, dy]) => isRoad(T_(x + dx, y + dy)))) continue;
    const dc = Math.hypot(x - 69.5, y - 37);
    const z = x >= 75 || (y >= 41 && x <= 65) ? "I" : dc < 2.6 ? "C" : "R"; const r = rnd();
    put(x, y, z, { lvl: z === "R" ? (r < .12 ? 2 : r < .55 ? 1 : 0) : z === "C" ? (r < .3 ? 2 : r < .85 ? 1 : 0) : (r < .75 ? 1 : 0) });
  }
  put(67, 36, "fire"); put(70, 38, "park");
  for (let x = 48; x <= 58; x++) { put(x, 43, "R"); put(x, 45, "R"); }
  for (let y = 25; y <= 29; y++) { put(69, y, "R"); put(71, y, "R"); }
  for (let x = 66; x <= 74; x++) if (x !== 70) { put(x, 23, "R"); put(x, 25, "R"); }
  // age the infrastructure
  S.tiles.forEach(t => { if (isRoad(t) && t.cond === 100) t.cond = 60 + rnd() * 32; });
  for (let y = 24; y <= 33; y++) { const t = T_(70, y); if (isBridge(t)) t.cond = 36; }
  S.tiles.forEach((t, i) => { if (isBridge(t) && i % W < 40) t.cond = 58; });
  // day one: a main break at the Neck cuts water to the whole peninsula
  let bx = 63, by = 42; if (!isRoad(T_(bx, by))) { for (const [x, y] of [[64, 42], [63, 43], [64, 41], [62, 43]]) if (isRoad(T_(x, y))) { bx = x; by = y; break; } }
  const bt = T_(bx, by); bt.fW = true; bt.cond = 32;
  addInc("main", bx, by, true);
  S.flags = { brk: [bx, by], bridge: [70, 31] };
  computeAll();
  if (guided) log(`Welcome to ${CITY}, Commissioner. You run public works for a small harbor town. Your first orders are in the orange panel.`, "good");
  else log(`Sandbox city founded. A water main just broke at the Neck, so the whole peninsula is short on water.`, "bad");
}
