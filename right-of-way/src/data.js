"use strict";
// ─── Right-of-Way · static data ─────────────────────────────────────────────
// Map, rules, catalogs. Everything here is constant; game state lives in S.

const W = 112, H = 80, TS = 16;
const GRASS = 0, SEA = 1, FRESH = 2, FOREST = 3, HILL = 4, MARSH = 5, BEACH = 6;
const TER_NAME = ["Open land", "Atlantic Ocean", "River", "Woodland", "Hillside", "Salt marsh", "Beach"];
const isWater = ter => ter === SEA || ter === FRESH;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const START_YEAR = 2027;
const CITY = "Bayford", REGION = "Commonwealth Bay";

const ZONE = {
  R: { name: "Residential", pop: [0, 12, 30, 60], jobs: [0, 0, 0, 0] },
  C: { name: "Commercial",  pop: [0, 0, 0, 0],    jobs: [0, 8, 20, 40] },
  I: { name: "Industrial",  pop: [0, 0, 0, 0],    jobs: [0, 12, 28, 45] },
};
const CAP = { power: 60, pump: 0.30, sewage: 0.26 };              // MW, MGD, MGD
const UPKEEP = { power: 150, pump: 80, sewage: 100, fire: 60, depot: 70, park: 5, levee: 1 };

// Road classes. `time` is travel-time per tile at free flow; `cap` is vehicles per peak hour.
const ROAD = {
  road: { name: "Street",  cap: 60,  time: 1.0,  upkeep: 1, decay: 0.025, build: 50 },
  ave:  { name: "Avenue",  cap: 160, time: 0.75, upkeep: 2, decay: 0.020, build: 250 },
  hwy:  { name: "Highway", cap: 500, time: 0.3,  upkeep: 5, decay: 0.015, build: 400 },
  ramp: { name: "Ramp",    cap: 120, time: 0.6,  upkeep: 3, decay: 0.020, build: 300 },
};
const CTL_FACTOR = { none: 0.6, signal: 0.85, round: 0.95 };      // intersection capacity multipliers
const RADIUS = { fire: 7, depot: 8, park: 4 };

const TOOLS = [
  { id: "inspect", name: "Inspect & pan", group: "Survey", cost: 0, key: "q", sw: "#FFFFFF", glyph: "?", desc: "Click a tile to inspect it. Drag to pan the map, scroll or pinch to zoom." },
  { id: "road", name: "Street", group: "Roads", cost: 50, key: "1", sw: "#6E737A", desc: "Two-lane street, $50 a tile (more on hills and marsh). Drag to lay a run. Streets carry power lines and water and sewer mains. Over water it becomes a bridge." },
  { id: "ave", name: "Avenue", group: "Roads", cost: 250, key: "2", sw: "#474B52", unlock: 500, desc: "Widen a street to four lanes. Capacity goes from 60 to 160 vehicles per hour." },
  { id: "hwy", name: "Highway", group: "Roads", cost: 400, key: "h", sw: "#2F3A48", unlock: 1200, desc: "Limited-access highway, 500 vehicles per hour. Buildings can't front it; traffic gets on and off only at ramps. Reach the map edge to connect Bayford to the region." },
  { id: "ramp", name: "Ramp", group: "Roads", cost: 300, key: "j", sw: "#5B6B7E", unlock: 1200, desc: "On/off ramp. Place next to a highway to link it to local streets." },
  { id: "tunnel", name: "Tunnel", group: "Roads", cost: 2500, key: "t", sw: "#3C4650", unlock: 2500, desc: "Bored tunnel under the harbor or river, $2,500 a tile. No deck to rust and no drawbridge, but it can leak." },
  { id: "signal", name: "Traffic signal", group: "Roads", cost: 350, key: "g", sw: "#E0B43A", glyph: "●", desc: "Signalize an intersection. Raises its capacity from 60% to 85% of the street and cuts crashes." },
  { id: "round", name: "Roundabout", group: "Roads", cost: 900, key: "k", sw: "#9DB39A", glyph: "○", desc: "Replace an intersection with a roundabout: 95% capacity, fewest crashes, no signal timing to maintain." },
  { id: "R", name: "Residential", group: "Zoning", cost: 20, key: "3", sw: "#EFD77A", glyph: "R", desc: "Zone for housing. Grows with street access, power and water, and when people want to move in." },
  { id: "C", name: "Commercial", group: "Zoning", cost: 20, key: "4", sw: "#E39A96", glyph: "C", desc: "Zone for shops and offices. Needs residents nearby." },
  { id: "I", name: "Industrial", group: "Zoning", cost: 20, key: "5", sw: "#B4A2D6", glyph: "I", desc: "Zone for factories and warehouses. Lots of jobs, but it lowers nearby land values." },
  { id: "power", name: "Power plant", group: "Utilities", cost: 3000, key: "6", sw: "#F2C14E", glyph: "PW", desc: "60 MW gas plant. Power flows along connected streets, so the plant must touch the network it feeds." },
  { id: "pump", name: "Water plant", group: "Utilities", cost: 1500, key: "7", sw: "#8DB8C7", glyph: "WT", desc: "0.30 MGD intake and treatment plant. Needs fresh water: a river or the reservoir, not the ocean." },
  { id: "sewage", name: "Sewage plant", group: "Utilities", cost: 2500, key: "8", sw: "#9FA88A", glyph: "WW", desc: "0.26 MGD wastewater plant. Must sit on the shore. Without enough capacity, sewers overflow and the state fines the city." },
  { id: "fire", name: "Fire station", group: "Services", cost: 1200, key: "9", sw: "#D9534F", glyph: "FD", desc: "Puts out fires within 7 tiles before they spread." },
  { id: "depot", name: "Works depot", group: "Services", cost: 1000, key: "0", sw: "#E8590C", glyph: "DPW", desc: "Adds a repair crew and does preventive maintenance on roads within 8 tiles. Preventive work costs far less than emergency repair." },
  { id: "park", name: "Park", group: "Services", cost: 200, key: "p", sw: "#7FB069", glyph: "♣", desc: "Raises land values and approval within 4 tiles." },
  { id: "levee", name: "Levee", group: "Services", cost: 150, key: "l", sw: "#A78B63", glyph: "LV", desc: "Earthen embankment or seawall on the shore. Protects this tile and its neighbors from river floods and storm surge." },
  { id: "hall", name: "City Hall", group: "Landmarks", cost: 6000, key: "", sw: "#C9B79C", glyph: "CH", proj: true, desc: "Commission a new City Hall. You'll choose between four architects' designs." },
  { id: "airfield", name: "Airfield", group: "Landmarks", cost: 30000, key: "", sw: "#BFC7CF", glyph: "✈", proj: true, unlock: 1500, desc: "A 5,000 ft runway and small terminal. Brings business travel and tourists. Needs flat land and clear runway approaches." },
  { id: "airport", name: "Int'l airport", group: "Landmarks", cost: 120000, key: "", sw: "#9AA6B2", glyph: "✈", proj: true, unlock: 6000, desc: "Two long runways and a major terminal. A regional economic engine, and a regional noise problem." },
  { id: "golf9", name: "Club, 9 holes", group: "Landmarks", cost: 15000, key: "", sw: "#8DBF72", glyph: "⛳", proj: true, unlock: 2000, desc: "A nine-hole course and clubhouse. Pick a golf course architect, then a clubhouse architect." },
  { id: "golf18", name: "Club, 18 holes", group: "Landmarks", cost: 35000, key: "", sw: "#5E9C4A", glyph: "⛳", proj: true, unlock: 4000, desc: "A full championship course. Raises land values across the neighborhood, and drinks a lot of water in summer." },
  { id: "repair", name: "Repair", group: "Maintain", cost: 0, key: "e", sw: "#FFFFFF", glyph: "🔧", desc: "Resurface a road or rehabilitate a bridge to full condition. Emergency rates: $6 per point on streets, $25 on bridges. Click a work order marker to dispatch a crew." },
  { id: "bulldoze", name: "Demolish", group: "Maintain", cost: 10, key: "x", sw: "#FFFFFF", glyph: "✕", desc: "Clear a tile, $10. Clicking a landmark demolishes the whole landmark." },
];
const TOOL = Object.fromEntries(TOOLS.map(t => [t.id, t]));

// Multi-tile landmarks. w×h is the unrotated footprint; `rpz` = runway protection zone length.
const PROJ = {
  hall:     { name: "City Hall", w: 3, h: 3, days: 60, jobs: 40, upkeep: 120, power: 0.8, water: 0.004, approval: 4 },
  airfield: { name: "Bayford Regional Airfield", w: 10, h: 3, days: 180, jobs: 150, upkeep: 600, power: 4, water: 0.02, rpz: 4, noise: 6, flat: true },
  airport:  { name: "Commonwealth Bay International", w: 16, h: 6, days: 360, jobs: 900, upkeep: 2500, power: 14, water: 0.08, rpz: 6, noise: 10, flat: true },
  golf9:    { name: "Country club", w: 10, h: 7, days: 120, jobs: 35, upkeep: 250, power: 1, water: 0.06, holes: 9 },
  golf18:   { name: "Country club", w: 15, h: 10, days: 200, jobs: 80, upkeep: 500, power: 2, water: 0.14, holes: 18 },
};

// Building architects. Multipliers on the base bid.
const ARCH = [
  { id: "bulfinch", firm: "Bulfinch Row Associates", style: "Federal Revival", pitch: "Red brick, white trim and a gilded cupola. It looks like it has always been here.",
    cost: 1.0, days: 1.0, upkeep: 1.0, approval: 6, prestige: 1.0, power: 1.0, colors: ["#A4473A", "#F4EFE4", "#D6A737"] },
  { id: "morrow", firm: "Halden Morrow Architects", style: "Glass Modernism", pitch: "A curtain-wall glass box under a cantilevered roof. Tourists will photograph it.",
    cost: 1.35, days: 1.15, upkeep: 1.25, approval: 2, prestige: 1.6, power: 1.2, colors: ["#7FA7BF", "#E7EEF2", "#2B3A48"] },
  { id: "ferro", firm: "Ferro & Castellan", style: "Brutalism", pitch: "Board-formed concrete built to stand for a century. Cheap to run. Some people will hate it.",
    cost: 0.85, days: 0.9, upkeep: 0.7, approval: -5, prestige: 0.8, power: 1.0, colors: ["#A3A09A", "#C9C6BF", "#6D6A65"] },
  { id: "greenline", firm: "Greenline Studio", style: "Mass Timber, Net Zero", pitch: "Cross-laminated timber, a planted roof and rooftop solar. Slower to build, nearly free to power.",
    cost: 1.2, days: 1.3, upkeep: 0.85, approval: 4, prestige: 1.2, power: 0.35, colors: ["#C8A27A", "#6E9B5A", "#3C4B3A"] },
];
const ARCH_BY = Object.fromEntries(ARCH.map(a => [a.id, a]));

// Golf course architects.
const GOLF = [
  { id: "dunmore", firm: "Dunmore Links Design", style: "Classic Links", pitch: "Firm, fast fairways through the dunes. Uses half the water of a parkland course. Must touch the ocean or a beach.",
    cost: 1.0, water: 0.5, members: 1.2, prestige: 1.5, coast: true },
  { id: "whitcombe", firm: "Whitcombe Parkland Co.", style: "Parkland", pitch: "Tree-lined fairways, lush greens and ponds. The members love it. Very thirsty in summer.",
    cost: 1.15, water: 1.3, members: 1.3, prestige: 1.1 },
  { id: "heather", firm: "Fescue & Heather Studio", style: "Heathland", pitch: "Native grasses and very little earthwork. The cheapest course to build and run.",
    cost: 0.75, water: 0.7, members: 0.85, prestige: 0.9 },
  { id: "ridgeline", firm: "Ridgeline Golf Partners", style: "Hillside", pitch: "Big elevation changes and long views. At least a quarter of the site must be hillside.",
    cost: 1.3, water: 1.0, members: 1.1, prestige: 1.4, hill: true },
];
const GOLF_BY = Object.fromEntries(GOLF.map(g => [g.id, g]));

const INC = {
  main:   { name: "Water main break",    days: 3,  cost: 800,  sev: 2, desc: "A cast-iron main failed under the street. Water can't flow past this point, and the city loses $25 a day in treated water." },
  sink:   { name: "Sinkhole",            days: 5,  cost: 1500, sev: 3, desc: "The roadway collapsed. Traffic, power and water can't pass this tile." },
  bridge: { name: "Bridge closed",       days: 12, cost: 6000, sev: 3, desc: "Inspection rated this bridge structurally deficient, so it's closed to traffic. If it keeps deteriorating it will collapse." },
  tunnel: { name: "Tunnel leak",         days: 6,  cost: 4000, sev: 3, desc: "Groundwater is coming through a failed joint. The tube is closed until it's grouted and sealed." },
  plant:  { name: "Power plant trip",    days: 4,  cost: 2000, sev: 3, desc: "A turbine tripped offline. Everything it fed is on reduced supply." },
  lines:  { name: "Power line down",     days: 2,  cost: 400,  sev: 2, desc: "Storm damage. Power can't pass this tile." },
  pump:   { name: "Water plant failure", days: 3,  cost: 1200, sev: 3, desc: "High-service pumps failed. This plant isn't producing water." },
  flood:  { name: "Flooded facility",    days: 6,  cost: 2500, sev: 3, desc: "Floodwater got into the plant. It's offline until it's pumped out and rebuilt." },
  fire:   { name: "Structure fire",      days: 1,  cost: 600,  sev: 2, desc: "No fire station covers this block, so the fire is spreading. Call mutual aid from a neighboring town, or build a fire station." },
  crash:  { name: "Traffic crash",       days: 0,  cost: 0,    sev: 1, auto: true, desc: "A crash at an uncontrolled, congested intersection. Police will clear it in a day or two. A signal or roundabout would prevent these." },
};

const MILESTONES = [
  { pop: 500,  text: "Avenues unlocked. Widen busy streets before they reach LOS F.", grant: 0 },
  { pop: 900,  text: "Town charter granted. State grant of $5,000.", grant: 5000 },
  { pop: 1200, text: "Highways and ramps unlocked. The state DOT will fund $10,000 toward a regional connection.", grant: 10000 },
  { pop: 1500, text: "The FAA will now fund a regional airfield. Look for flat land with clear approaches.", grant: 0 },
  { pop: 2000, text: "Bayford is attracting wealthy families. Nine-hole country clubs are now available.", grant: 5000 },
  { pop: 2500, text: "Tunnels unlocked. Federal infrastructure grant of $15,000.", grant: 15000 },
  { pop: 4000, text: "City status. Eighteen-hole country clubs are available.", grant: 20000 },
  { pop: 6000, text: "Metropolitan status. You can now build an international airport.", grant: 40000 },
];

// District labels drawn on the map, loosely after the places they borrow from.
const DISTRICTS = [
  { name: "OLD BAYFORD", x: 69, y: 37.5, size: 11 },
  { name: "BACK MARSH", x: 57, y: 38.5, size: 9 },
  { name: "NORTHBANK", x: 62, y: 22, size: 11 },
  { name: "EAST FLATS", x: 86, y: 28, size: 10 },
  { name: "BAYFORD HARBOR", x: 80, y: 45, size: 10, water: true },
  { name: "QUILL RIVER", x: 40, y: 27.2, size: 9, water: true },
  { name: "IRON RIVER", x: 20, y: 58, size: 9, water: true },
  { name: "THREE RIVERS POINT", x: 29, y: 35.5, size: 9 },
  { name: "IRON HEIGHTS", x: 12, y: 46, size: 11 },
  { name: "QUARRY HILLS", x: 44, y: 64, size: 11 },
  { name: "BROOKFIELD", x: 26, y: 12, size: 11 },
  { name: "SOUTH SHORE", x: 72, y: 60, size: 10 },
  { name: "MARROW ISLAND", x: 101, y: 72.5, size: 9 },
  { name: "ATLANTIC OCEAN", x: 101, y: 20, size: 12, water: true },
  { name: "QUARRY RESERVOIR", x: 12, y: 66.5, size: 8, water: true },
];
