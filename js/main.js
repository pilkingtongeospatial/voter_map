// Application entry point.
// Wires together data loading, map rendering, and sidebar panel rendering.
// All DOM mutation happens in this module; every other module is pure.

import {
  initMaps,
  buildStateLayer,
  addInsetStateLayers,
  buildStateLabels,
  buildCdLayer,
  buildStateLegLayer,
} from "./map.js";
import {
  welcomePanelHtml,
  statePanelHtml,
  districtPanelHtml,
  stateLegDistrictPanelHtml,
} from "./panels.js";
import {
  districtNumFromProps,
  stateLegDistrictFromProps,
  stateLegMeta,
  hasLowerChamber,
} from "./utils.js";

// ── mutable module-level state ────────────────────────────────────────────────

let map, akMap, hiMap;
let statesGJ, cdGJ, cdGJ_119, sldUpperGJ, sldLowerGJ;
let legislators, stateLegislators, stateMeta;
let stateLayer = null;
let cdLayer = null;
let stateLegLayer = null;
let labelMarkers = [];
let selectedStateAbbr = null;
let viewMode = "current"; // "current" | "2026" | "state_upper" | "state_lower"

const FEDERAL_MODES = new Set(["current", "2026"]);
const STATE_MODES = new Set(["state_upper", "state_lower"]);

/**
 * Coerce viewMode to one that's valid for the given state.
 *  - "state_lower" in a unicameral state (NE) → "state_upper"
 *  - "state_*"     in a state with no legMeta (DC, territories) → "current"
 *  - anything else → unchanged
 */
function normalizeViewModeForState(abbr, mode) {
  if (FEDERAL_MODES.has(mode)) return mode;
  if (!stateLegMeta(abbr)) return "current";
  if (mode === "state_lower" && !hasLowerChamber(abbr)) return "state_upper";
  return mode;
}

// ── panel rendering ───────────────────────────────────────────────────────────

function renderPanel(html) {
  document.getElementById("sidebar-content").innerHTML = html;
}

function showWelcome() { renderPanel(welcomePanelHtml()); }

function showState(abbr, stateName) {
  const meta = stateMeta[abbr] || {};
  const leg = legislators[abbr] || {};
  const senators = leg.senators || [];
  renderPanel(statePanelHtml(abbr, stateName, meta, senators, viewMode));
}

function showDistrict(stateAbbr, districtNum, districtLabel) {
  const meta = stateMeta[stateAbbr] || {};
  const leg = legislators[stateAbbr] || {};
  const reps = leg.representatives || {};
  const rep = reps[String(districtNum)] || reps["0"] || null;
  renderPanel(districtPanelHtml(stateAbbr, districtNum, districtLabel, rep, meta.voter_reg || {}, viewMode));

  // Highlight the clicked district on the map
  if (cdLayer) {
    cdLayer.eachLayer((l) => {
      const d = districtNumFromProps(l.feature.properties);
      if (d === districtNum) {
        l.setStyle({ fillOpacity: 0.85, weight: 3, color: "#ffeb3b" });
      } else {
        cdLayer.resetStyle(l);
      }
    });
  }
}

function showStateLegDistrict(stateAbbr, chamber, district) {
  const meta = stateMeta[stateAbbr] || {};
  const member = (((stateLegislators[stateAbbr] || {})[chamber]) || {})[district] || null;
  renderPanel(stateLegDistrictPanelHtml(stateAbbr, chamber, district, member, meta.voter_reg || {}));

  if (stateLegLayer) {
    stateLegLayer.eachLayer((l) => {
      const d = stateLegDistrictFromProps(l.feature.properties, chamber);
      if (d === district) {
        l.setStyle({ fillOpacity: 0.85, weight: 3, color: "#ffeb3b" });
      } else {
        stateLegLayer.resetStyle(l);
      }
    });
  }
}

// ── map interactions ──────────────────────────────────────────────────────────

function clearDistrictLayers() {
  if (cdLayer) { map.removeLayer(cdLayer); cdLayer = null; }
  if (stateLegLayer) { map.removeLayer(stateLegLayer); stateLegLayer = null; }
}

/**
 * Build whichever district layer matches the current viewMode for the
 * selected state. Caller is responsible for clearing any prior layers.
 */
function buildLayerForCurrentView(abbr) {
  if (viewMode === "current") {
    cdLayer = buildCdLayer(map, cdGJ_119, abbr, legislators, { click: onDistrictClick });
  } else if (viewMode === "2026") {
    cdLayer = buildCdLayer(map, cdGJ, abbr, legislators, { click: onDistrictClick });
  } else if (viewMode === "state_upper") {
    stateLegLayer = buildStateLegLayer(map, sldUpperGJ, abbr, "upper", stateLegislators,
      { click: onStateLegDistrictClick });
  } else if (viewMode === "state_lower") {
    stateLegLayer = buildStateLegLayer(map, sldLowerGJ, abbr, "lower", stateLegislators,
      { click: onStateLegDistrictClick });
  }
}

function onStateClick(feat, layer) {
  const abbr = feat.properties.abbr;
  if (!abbr) return;
  selectedStateAbbr = abbr;

  // Carry the user's mode preference, but normalize for unicameral / no-meta states.
  viewMode = normalizeViewModeForState(abbr, viewMode);

  const bounds = layer.getBounds();
  map.fitBounds(bounds, { padding: [40, 40], maxZoom: 8 });

  stateLayer.eachLayer((l) => {
    const a = l.feature.properties.abbr;
    if (a !== abbr) l.setStyle({ fillOpacity: 0.15, weight: 1, color: "#ccc" });
    else l.setStyle({ fillOpacity: 0, weight: 2.5, color: "#fff" });
  });

  clearDistrictLayers();
  buildLayerForCurrentView(abbr);
  showState(abbr, feat.properties.name);
}

function onDistrictClick(feat, stateAbbr) {
  const props = feat.properties;
  const cdNum = districtNumFromProps(props);
  const label = props.NAMELSAD || props.namelsad || `District ${cdNum}`;
  showDistrict(stateAbbr, cdNum, label);
}

function onStateLegDistrictClick(feat, stateAbbr, chamber) {
  const district = stateLegDistrictFromProps(feat.properties, chamber);
  showStateLegDistrict(stateAbbr, chamber, district);
}

function resetToNational() {
  selectedStateAbbr = null;
  map.flyTo([39.5, -97.5], 4, { duration: 0.8 });
  stateLayer.eachLayer((l) => stateLayer.resetStyle(l));
  clearDistrictLayers();
  showWelcome();
}

function switchView(mode) {
  if (viewMode === mode) return;
  if (selectedStateAbbr) {
    mode = normalizeViewModeForState(selectedStateAbbr, mode);
  }
  viewMode = mode;
  clearDistrictLayers();
  if (selectedStateAbbr) {
    buildLayerForCurrentView(selectedStateAbbr);
    // Re-render the sidebar so the toggle's active class + click hint update
    showState(selectedStateAbbr, stateNameFromAbbr(selectedStateAbbr));
  }
}

function stateNameFromAbbr(abbr) {
  const f = statesGJ.features.find((x) => x.properties.abbr === abbr);
  return f ? f.properties.name : abbr;
}

function backToState(abbr) {
  showState(abbr, stateNameFromAbbr(abbr));
  // Re-dim non-selected states
  stateLayer.eachLayer((l) => {
    const a = l.feature.properties.abbr;
    if (a !== abbr) l.setStyle({ fillOpacity: 0.15, weight: 1, color: "#ccc" });
    else l.setStyle({ fillOpacity: 0.7, weight: 2.5, color: "#fff" });
  });
  if (cdLayer) cdLayer.eachLayer((l) => cdLayer.resetStyle(l));
  if (stateLegLayer) stateLegLayer.eachLayer((l) => stateLegLayer.resetStyle(l));
}

// ── delegated event handling for sidebar buttons ──────────────────────────────

function handleSidebarClick(e) {
  const btn = e.target.closest("[data-action]");
  if (!btn) return;
  const action = btn.dataset.action;
  if (action === "reset-national") resetToNational();
  else if (action === "switch-view") switchView(btn.dataset.view);
  else if (action === "back-to-state") backToState(btn.dataset.abbr);
}

// ── state-layer hover handlers (extracted so buildStateLayer stays generic) ──

const stateHoverHandlers = {
  mouseover(e) {
    if (selectedStateAbbr) return;
    e.target.setStyle({ fillOpacity: 0.75, weight: 2.5 });
  },
  mouseout(e, feat, leaf, layer) {
    if (selectedStateAbbr) return;
    layer.resetStyle(e.target);
  },
  click: onStateClick,
};

// ── data loading ──────────────────────────────────────────────────────────────

async function loadAll() {
  const msgs = [
    "Loading state boundaries…",
    "Loading congressional districts…",
    "Loading state legislative districts…",
    "Loading legislator data…",
    "Loading state metadata…",
  ];
  let i = 0;
  const loadingMsg = document.getElementById("loading-msg");
  const tick = setInterval(() => {
    if (i < msgs.length) loadingMsg.textContent = msgs[i++];
  }, 600);

  [
    statesGJ,
    cdGJ_119,
    cdGJ,
    sldUpperGJ,
    sldLowerGJ,
    legislators,
    stateLegislators,
    stateMeta,
  ] = await Promise.all([
    fetch("data/states.geojson").then((r) => r.json()),
    fetch("data/congressional_districts_119.geojson").then((r) => r.json()),
    fetch("data/congressional_districts.geojson").then((r) => r.json()),
    fetch("data/state_leg_upper.geojson").then((r) => r.json()),
    fetch("data/state_leg_lower.geojson").then((r) => r.json()),
    fetch("data/legislators.json").then((r) => r.json()),
    fetch("data/state_legislators.json").then((r) => r.json()),
    fetch("data/state_meta.json").then((r) => r.json()),
  ]);

  clearInterval(tick);
  document.getElementById("loading").style.display = "none";

  stateLayer = buildStateLayer(map, statesGJ, stateHoverHandlers);
  labelMarkers = buildStateLabels(map);
  addInsetStateLayers(akMap, hiMap, statesGJ, onStateClick);
}

// ── bootstrap ─────────────────────────────────────────────────────────────────

({ map, akMap, hiMap } = initMaps());

document
  .getElementById("sidebar-content")
  .addEventListener("click", handleSidebarClick);

loadAll().catch((err) => {
  console.error(err);
  const msg = document.getElementById("loading-msg");
  if (msg) {
    msg.textContent =
      "Error loading data. Make sure you are running serve.py and data has been downloaded.";
  }
});
