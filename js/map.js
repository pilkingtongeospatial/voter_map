// Leaflet-dependent layer builders and map initialization.
// Not unit-tested (requires a real browser/Leaflet). Pure logic it uses
// (styling, district-number parsing) lives in utils.js and IS tested.

import { PARTY_COLOR, STATE_CENTROIDS } from "./constants.js";
import {
  stateStyle,
  abbrToFips,
  districtNumFromProps,
} from "./utils.js";

const BASEMAP_URL = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png";
const BASEMAP_ATTR =
  '&copy; <a href="https://carto.com/">CARTO</a> | US Census TIGER | congress-legislators';

/**
 * Create the three Leaflet map instances. Returns { map, akMap, hiMap }.
 * Caller must have already loaded Leaflet (L must be a global).
 */
export function initMaps() {
  const map = L.map("map", {
    center: [39.5, -97.5], zoom: 4, minZoom: 3,
    zoomControl: true, attributionControl: true,
  });
  L.tileLayer(BASEMAP_URL, {
    attribution: BASEMAP_ATTR, subdomains: "abcd", maxZoom: 19,
  }).addTo(map);

  const insetOpts = {
    zoomControl: false, attributionControl: false,
    dragging: false, scrollWheelZoom: false,
    doubleClickZoom: false, boxZoom: false,
    keyboard: false, touchZoom: false,
  };

  const akMap = L.map("inset-ak", { center: [64, -153], zoom: 2, ...insetOpts });
  L.tileLayer(BASEMAP_URL, { subdomains: "abcd", maxZoom: 19 }).addTo(akMap);

  const hiMap = L.map("inset-hi", { center: [20.5, -157], zoom: 5, ...insetOpts });
  L.tileLayer(BASEMAP_URL, { subdomains: "abcd", maxZoom: 19 }).addTo(hiMap);

  return { map, akMap, hiMap };
}

/**
 * Build and add the main state layer (excluding AK and HI).
 * Returns the layer so the caller can manipulate it (e.g. on click).
 */
export function buildStateLayer(map, statesGJ, handlers) {
  const mainFeatures = statesGJ.features.filter(
    (f) => f.properties.abbr !== "AK" && f.properties.abbr !== "HI"
  );
  const mainGJ = { type: "FeatureCollection", features: mainFeatures };

  let layer;
  layer = L.geoJSON(mainGJ, {
    style: stateStyle,
    onEachFeature(feat, leaf) {
      leaf.on({
        mouseover(e) { handlers.mouseover(e, feat, leaf, layer); },
        mouseout(e) { handlers.mouseout(e, feat, leaf, layer); },
        click() { handlers.click(feat, leaf); },
      });
    },
  }).addTo(map);
  return layer;
}

/**
 * Add AK and HI state layers to their respective inset maps.
 */
export function addInsetStateLayers(akMap, hiMap, statesGJ, onStateClick) {
  const akFeat = statesGJ.features.filter((f) => f.properties.abbr === "AK");
  L.geoJSON({ type: "FeatureCollection", features: akFeat }, {
    style: stateStyle,
    onEachFeature(feat, leaf) { leaf.on("click", () => onStateClick(feat, leaf)); },
  }).addTo(akMap);

  const hiFeat = statesGJ.features.filter((f) => f.properties.abbr === "HI");
  L.geoJSON({ type: "FeatureCollection", features: hiFeat }, {
    style: stateStyle,
    onEachFeature(feat, leaf) { leaf.on("click", () => onStateClick(feat, leaf)); },
  }).addTo(hiMap);
}

/**
 * Add state-abbreviation label markers to the main map.
 * Returns the array of markers so the caller can clear them if needed.
 */
export function buildStateLabels(map) {
  const markers = [];
  Object.entries(STATE_CENTROIDS).forEach(([abbr, latlng]) => {
    if (abbr === "AK" || abbr === "HI") return;
    const icon = L.divIcon({
      html: `<div class="state-label">${abbr}</div>`,
      className: "", iconSize: [28, 16], iconAnchor: [14, 8],
    });
    const m = L.marker(latlng, { icon, interactive: false, zIndexOffset: 100 });
    m.addTo(map);
    markers.push(m);
  });
  return markers;
}

/**
 * Build the congressional-district layer for a single state.
 * Returns the layer (may be null if no matching features are found).
 */
export function buildCdLayer(map, sourceGJ, abbr, legislators, handlers) {
  const fips = abbrToFips(abbr);
  if (!fips) return null;

  const stateFeats = sourceGJ.features.filter(
    (f) => (f.properties.STATEFP || f.properties.statefp) === fips
  );
  if (!stateFeats.length) return null;

  let cdLayer;
  cdLayer = L.geoJSON({ type: "FeatureCollection", features: stateFeats }, {
    style(cdFeat) {
      const cdNum = districtNumFromProps(cdFeat.properties);
      const rep = ((legislators[abbr] || {}).representatives || {})[String(cdNum)] || null;
      const party = rep ? (rep.party || "") : "";
      const fill = party.toLowerCase().includes("republican") ? PARTY_COLOR.R
                 : party.toLowerCase().includes("democrat")   ? PARTY_COLOR.D
                 : "#888";
      return { fillColor: fill, fillOpacity: 0.55, color: "#fff", weight: 1.5, opacity: 1 };
    },
    onEachFeature(cdFeat, leaf) {
      leaf.on({
        mouseover(e) { e.target.setStyle({ fillOpacity: 0.8, weight: 2.5 }); },
        mouseout(e) { cdLayer.resetStyle(e.target); },
        click(e) { handlers.click(cdFeat, abbr); L.DomEvent.stopPropagation(e); },
      });
    },
  }).addTo(map);
  return cdLayer;
}
