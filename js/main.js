// Application entry point.
// Wires together data loading, map rendering, and sidebar panel rendering.
// All DOM mutation happens in this module; every other module is pure.

import {
  initMaps,
  buildStateLayer,
  addInsetStateLayers,
  buildStateLabels,
  buildCdLayer,
} from "./map.js";
import {
  welcomePanelHtml,
  statePanelHtml,
  districtPanelHtml,
} from "./panels.js";
import { districtNumFromProps } from "./utils.js";

// ── mutable module-level state ────────────────────────────────────────────────

let map, akMap, hiMap;
let statesGJ, cdGJ, cdGJ_119, legislators, stateMeta;
let stateLayer = null;
let cdLayer = null;
let labelMarkers = [];
let selectedStateAbbr = null;
let viewMode = "current"; // "current" | "2026"

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

// ── map interactions ──────────────────────────────────────────────────────────

function onStateClick(feat, layer) {
  const abbr = feat.properties.abbr;
  if (!abbr) return;
  selectedStateAbbr = abbr;

  const bounds = layer.getBounds();
  map.fitBounds(bounds, { padding: [40, 40], maxZoom: 8 });

  stateLayer.eachLayer((l) => {
    const a = l.feature.properties.abbr;
    if (a !== abbr) l.setStyle({ fillOpacity: 0.15, weight: 1, color: "#ccc" });
    else l.setStyle({ fillOpacity: 0, weight: 2.5, color: "#fff" });
  });

  if (cdLayer) { map.removeLayer(cdLayer); cdLayer = null; }

  const source = viewMode === "2026" ? cdGJ : cdGJ_119;
  cdLayer = buildCdLayer(map, source, abbr, legislators, {
    click: onDistrictClick,
  });
  showState(abbr, feat.properties.name);
}

function onDistrictClick(feat, stateAbbr) {
  const props = feat.properties;
  const cdNum = districtNumFromProps(props);
  const label = props.NAMELSAD || props.namelsad || `District ${cdNum}`;
  showDistrict(stateAbbr, cdNum, label);
}

function resetToNational() {
  selectedStateAbbr = null;
  map.flyTo([39.5, -97.5], 4, { duration: 0.8 });
  stateLayer.eachLayer((l) => stateLayer.resetStyle(l));
  if (cdLayer) { map.removeLayer(cdLayer); cdLayer = null; }
  showWelcome();
}

function switchView(mode) {
  if (viewMode === mode) return;
  viewMode = mode;
  if (cdLayer) { map.removeLayer(cdLayer); cdLayer = null; }
  if (selectedStateAbbr) {
    const source = viewMode === "2026" ? cdGJ : cdGJ_119;
    cdLayer = buildCdLayer(map, source, selectedStateAbbr, legislators, {
      click: onDistrictClick,
    });
  }
  // Update active class on the toggle buttons in the sidebar
  document.querySelectorAll(".view-toggle button").forEach((b) => {
    b.classList.toggle("active", b.dataset.mode === mode);
  });
}

function backToState(abbr) {
  const feat = statesGJ.features.find((f) => f.properties.abbr === abbr);
  const name = feat ? feat.properties.name : abbr;
  showState(abbr, name);
  // Re-dim non-selected states
  stateLayer.eachLayer((l) => {
    const a = l.feature.properties.abbr;
    if (a !== abbr) l.setStyle({ fillOpacity: 0.15, weight: 1, color: "#ccc" });
    else l.setStyle({ fillOpacity: 0.7, weight: 2.5, color: "#fff" });
  });
  if (cdLayer) cdLayer.eachLayer((l) => cdLayer.resetStyle(l));
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
    "Loading current districts…",
    "Loading 2026 expected districts…",
    "Loading legislator data…",
    "Loading state metadata…",
  ];
  let i = 0;
  const loadingMsg = document.getElementById("loading-msg");
  const tick = setInterval(() => {
    if (i < msgs.length) loadingMsg.textContent = msgs[i++];
  }, 600);

  [statesGJ, cdGJ_119, cdGJ, legislators, stateMeta] = await Promise.all([
    fetch("data/states.geojson").then((r) => r.json()),
    fetch("data/congressional_districts_119.geojson").then((r) => r.json()),
    fetch("data/congressional_districts.geojson").then((r) => r.json()),
    fetch("data/legislators.json").then((r) => r.json()),
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
