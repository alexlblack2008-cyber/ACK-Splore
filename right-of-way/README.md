# Right-of-Way

A civil engineering city simulation. You're the Commissioner of Public Works for **Bayford**, a harbor town in the made-up region of **Commonwealth Bay**. Grow it into a city, and keep its streets, bridges, water, power and sewers from falling apart while you do.

The region is a composite, the way GTA's cities stitch real places together:

| District | Borrowed from |
| --- | --- |
| Old Bayford: a crooked colonial peninsula joined to the mainland by a narrow Neck | Boston |
| Back Marsh (fill it before you build), Northbank across the river | Back Bay, Cambridge |
| East Flats: tidal marsh across the harbor, the natural airport site | Logan Airport |
| Three Rivers Point, Iron Heights | Pittsburgh's confluence and steel hills |
| Brookfield: rolling woods for a country club | Brookline's The Country Club |
| Marrow Island, the South Shore beaches | Nantucket, Cape Cod |

## Playing

Open `index.html` in a browser. There's no build step and nothing to install. To serve it locally instead:

```sh
python3 -m http.server 8000   # then visit http://localhost:8000
```

Pick **Guided start** the first time. The Mayor's office walks you through thirteen orders, from fixing a broken water main to opening an airfield and a country club. Each order pays a grant, and nothing random goes wrong during your first year.

### What you manage

- **Streets are the right-of-way.** Power lines and water and sewer mains run under them, so a plant only serves buildings on the street network it touches. One broken main can cut off a neighborhood.
- **Traffic is routed.** Commuters take the fastest path to jobs. Congestion slows a route along the Bureau of Public Roads (BPR) volume-delay curve, so a new highway or avenue pulls traffic off side streets. Highways connect only through ramps. Uncontrolled intersections lose 40% of their capacity until you add a signal or a roundabout. Tunnels cross under the harbor.
- **Everything wears out.** Pavement is rated by PCI, bridges by the NBI 0–9 scale. Traffic and freeze-thaw wear roads down. Old streets break mains and open sinkholes. A bridge below NBI 3 closes, and an ignored closed bridge collapses.
- **Things go wrong** on a real calendar: nor'easters in winter, pothole season from February to April, spring river floods, summer heat waves, fall hurricanes, plant trips, fires and crashes. Each incident becomes a work order that a crew has to fix.
- **Landmarks go out to bid.** City Hall, a regional airfield, an international airport and 9- or 18-hole country clubs each get proposals from competing architects. The four building firms work in Federal Revival, Glass Modernism, Brutalism and Mass Timber, and differ in cost, build time, upkeep, public reaction, visitor appeal and energy use. Golf courses add a second round with four course designers (links, parkland, heathland, hillside). Each firm has its own site rules and summer irrigation needs.
- **Airports** need flat land, a street, and runway protection zones clear of tall buildings. A highway ramp nearby brings in more passengers. The noise lowers nearby land values.

### Saving

- The game **autosaves** every in-game month and whenever you leave or hide the page.
- **Save** in the top bar has three manual slots plus the autosave.
- When the game runs as a claude.ai artifact, saves also go to **your claude.ai account**, so you can continue on another device. Otherwise they stay in the browser.
- **Export save file** gives you a backup file (or a save code) that you can load on any device with **Load from file**.

## Code layout

| File | What's in it |
| --- | --- |
| `src/data.js` | Map size, catalogs: road classes, tools, landmarks, architects, incidents, milestones |
| `src/world.js` | Terrain generation and the starting town |
| `src/sim.js` | Utility networks, traffic assignment, land value, weather, incidents, economy, construction |
| `src/projects.js` | Architect RFPs, landmark siting, elevation and golf-routing drawings |
| `src/render.js` | Canvas camera, terrain cache with survey contours, overlays, minimap |
| `src/save.js` | Compact save format, browser and account storage, export and import |
| `src/tutorial.js` | Guided start |
| `src/ui.js` | Panels, input, main loop |
