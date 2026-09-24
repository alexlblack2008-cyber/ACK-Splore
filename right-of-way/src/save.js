"use strict";
// ─── Right-of-Way · saving ──────────────────────────────────────────────────
// Every save goes to this browser (localStorage). When the game runs as a
// claude.ai artifact, saves also go to your account, so they follow you
// between devices. You can also export a save file and load it anywhere.

const SAVE_PREFIX = "right-of-way:v2:";
const SLOTS = [["auto", "Autosave"], ["s1", "Slot 1"], ["s2", "Slot 2"], ["s3", "Slot 3"]];
const B_CODES = [null, "road", "ave", "hwy", "ramp", "R", "C", "I", "power", "pump", "sewage", "fire", "depot", "park", "levee", "proj"];
let cloud = null, cloudUid = null, downloads = null, lastCloud = 0, cloudBusy = false;
let saveStatus = { at: 0, cloud: false, error: "" };

function b64(u8) { let s = ""; for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000)); return btoa(s); }
function unb64(str) { const s = atob(str), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return u; }

function encodeState() {
  const u = new Uint8Array(W * H * 12);
  S.tiles.forEach((t, i) => {
    const o = i * 12;
    u[o] = t.ter; u[o + 1] = Math.max(0, B_CODES.indexOf(t.b)); u[o + 2] = t.lvl; u[o + 3] = Math.round(t.cond);
    u[o + 4] = (t.fW ? 1 : 0) | (t.fP ? 2 : 0) | (t.sink ? 4 : 0) | (t.closed ? 8 : 0) | (t.off ? 16 : 0);
    u[o + 5] = t.st === "bridge" ? 1 : t.st === "tunnel" ? 2 : 0; u[o + 6] = t.ctl === "signal" ? 1 : t.ctl === "round" ? 2 : 0;
    u[o + 7] = t.pid & 255; u[o + 8] = (t.pid >> 8) & 255; u[o + 9] = Math.min(255, t.fire); u[o + 10] = Math.min(255, t.flood); u[o + 11] = Math.min(255, t.bad);
  });
  const rest = {};
  for (const k in S) if (k !== "tiles" && k !== "net" && k !== "grades" && !k.startsWith("_")) rest[k] = S[k];
  rest.news = S.news.slice(0, 30);
  return { v: 2, savedAt: Date.now(), day: S.day, pop: S.pop, funds: Math.round(S.funds), city: S.cityName || CITY, tiles: b64(u), state: JSON.stringify(rest) };
}
function decodeState(sv) {
  if (!sv || sv.v !== 2 || !sv.tiles || !sv.state) throw new Error("Not a Right-of-Way save");
  const rest = JSON.parse(sv.state), u = unb64(sv.tiles), E = elevations(rest.seed);
  if (u.length !== W * H * 12) throw new Error("Save is from a different map size");
  const tiles = [];
  for (let i = 0; i < W * H; i++) {
    const o = i * 12, t = newTile(u[o], E[i]), f = u[o + 4];
    Object.assign(t, { b: B_CODES[u[o + 1]] ?? null, lvl: u[o + 2], cond: u[o + 3], fW: !!(f & 1), fP: !!(f & 2), sink: !!(f & 4), closed: !!(f & 8), off: !!(f & 16),
      st: [null, "bridge", "tunnel"][u[o + 5]], ctl: [null, "signal", "round"][u[o + 6]], pid: u[o + 7] | (u[o + 8] << 8), fire: u[o + 9], flood: u[o + 10], bad: u[o + 11] });
    tiles.push(t);
  }
  S = Object.assign(rest, { tiles, _elev: E });
  S.counters = S.counters || {}; S.unlocked = S.unlocked || {}; S.tut = S.tut || { on: false, step: 0, done: [], seen: {} };
  markRPZ(); computeAll(); terrainDirty = true;
}

// ── local ────────────────────────────────────────────────────────────────────
function localPut(slot, sv) { try { localStorage.setItem(SAVE_PREFIX + slot, JSON.stringify(sv)); return true; } catch (e) { return false; } }
function localGet(slot) { try { const s = localStorage.getItem(SAVE_PREFIX + slot); return s ? JSON.parse(s) : null; } catch (e) { return null; } }

// ── your claude.ai account ───────────────────────────────────────────────────
async function initCloud() {
  try {
    if (!window.claude || typeof window.claude.use !== "function") return;
    const dl = window.claude.use("downloads").then(d => { downloads = d; }).catch(() => {});
    const [db, user] = await Promise.all([window.claude.use("db"), window.claude.use("user")]);
    await dl;
    if (!db || !user) return;
    const id = await user.id(); if (!id) return;
    cloud = db; cloudUid = id;
    if (typeof renderSaveStatus === "function") renderSaveStatus();
  } catch (e) {}
}
const cloudDoc = slot => cloud.doc(`data/users/${cloudUid}/save-${slot}`);
async function cloudPut(slot, sv) {
  if (!cloud || cloudBusy) return false;
  cloudBusy = true;
  try { await cloudDoc(slot).set(sv); lastCloud = Date.now(); return true; }
  catch (e) { saveStatus.error = e && e.code === "invalid_argument" ? "Your account can't save to this copy" : "Account save failed"; return false; }
  finally { cloudBusy = false; }
}
async function cloudGet(slot) { if (!cloud) return null; try { const d = await cloudDoc(slot).get(); return d.exists ? d.data() : null; } catch (e) { return null; } }

// ── public API ───────────────────────────────────────────────────────────────
async function saveTo(slot, { quiet = false, cloudToo = true } = {}) {
  const sv = encodeState();
  const okLocal = localPut(slot, sv);
  saveStatus = { at: Date.now(), cloud: false, error: okLocal ? "" : "Browser storage is full or blocked" };
  if (cloudToo && cloud) saveStatus.cloud = await cloudPut(slot, sv);
  if (!quiet) log(`Game saved to ${SLOTS.find(s => s[0] === slot)[1]}${saveStatus.cloud ? " (this browser and your account)" : okLocal ? " (this browser)" : ""}.`, "good");
  if (typeof renderSaveStatus === "function") renderSaveStatus();
  return okLocal || saveStatus.cloud;
}
function autosave() { saveTo("auto", { quiet: true, cloudToo: Date.now() - lastCloud > 60000 }); }
async function newestSave(slot = "auto") {
  const a = localGet(slot), b = await cloudGet(slot);
  if (a && b) return a.savedAt >= b.savedAt ? a : b;
  return a || b;
}
async function slotInfo() {
  const out = [];
  for (const [id, name] of SLOTS) { const sv = await newestSave(id); out.push({ id, name, sv }); }
  return out;
}
function saveLabel(sv) {
  if (!sv) return "Empty";
  const ago = Math.round((Date.now() - sv.savedAt) / 60000);
  return `${dateStr(sv.day)} · ${(sv.pop || 0).toLocaleString()} residents · ${money(sv.funds)} · saved ${ago < 1 ? "just now" : ago < 60 ? ago + " min ago" : ago < 1440 ? Math.round(ago / 60) + " h ago" : Math.round(ago / 1440) + " d ago"}`;
}
async function exportSave() {
  const text = JSON.stringify(encodeState());
  if (downloads) {
    try { await downloads.save({ filename: `${(S.cityName || CITY).toLowerCase()}-${START_YEAR + Math.floor(S.day / 360)}.rowsave.json`, data: text }); log("Save file exported.", "good"); return; }
    catch (e) { if (e && e.code === "cancelled") return; }
  }
  try { await navigator.clipboard.writeText(text); log("Save code copied to the clipboard. Paste it into Load from file or code on any device.", "good"); }
  catch (e) { flash("Couldn't copy. Use the text box instead."); const ta = $("saveCode"); if (ta) { ta.hidden = false; ta.value = text; ta.select(); } }
}
function importSave(text) {
  try { decodeState(JSON.parse(text)); afterLoad(); log("Save loaded.", "good"); return true; }
  catch (e) { flash(e.message || "That isn't a valid save"); return false; }
}
window.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden" && S && S.day > 0) saveTo("auto", { quiet: true }); });
