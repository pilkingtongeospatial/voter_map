// Pure utility functions. No DOM access, no Leaflet dependency.
// Every function here is deterministic: same input → same output.

import {
  PARTY_COLOR,
  FIPS_TO_ABBR,
  ABBR_TO_FIPS,
  ABBR_TO_BALLOTPEDIA_STATE,
} from "./constants.js";

/**
 * Map a party name string to a CSS class name.
 * @param {string|null|undefined} party
 * @returns {string} "party-r" | "party-d" | "party-i" | ""
 */
export function partyClass(party) {
  if (!party) return "";
  const p = String(party).toLowerCase();
  if (p.includes("republican")) return "party-r";
  if (p.includes("democrat")) return "party-d";
  return "party-i";
}

/**
 * Leaflet style object for a state feature, colored by 2024 election result.
 * @param {object} feat - GeoJSON feature with properties.party
 */
export function stateStyle(feat) {
  const party = (feat && feat.properties && feat.properties.party) || "";
  const color = PARTY_COLOR[party] || "#888";
  return {
    fillColor: color,
    fillOpacity: 0.55,
    color: "#fff",
    weight: 1.5,
    opacity: 1,
  };
}

/**
 * Look up the 2-digit FIPS code for a state abbreviation.
 * @returns {string|null} FIPS code or null if unknown.
 */
export function abbrToFips(abbr) {
  return ABBR_TO_FIPS[abbr] || null;
}

/**
 * Look up the state abbreviation for a FIPS code.
 * @returns {string} abbreviation or "" if unknown.
 */
export function fipsToAbbr(fips) {
  return FIPS_TO_ABBR[fips] || "";
}

/**
 * Build a Ballotpedia URL for a congressional district race.
 * District 0 is treated as "at_Large".
 * @param {string} stateAbbr e.g. "CA"
 * @param {number} districtNum e.g. 12 (0 for at-large)
 * @param {number} year e.g. 2026
 */
export function ballotpediaUrl(stateAbbr, districtNum, year) {
  const bpState = ABBR_TO_BALLOTPEDIA_STATE[stateAbbr] || stateAbbr;
  const distStr = districtNum === 0 ? "at_Large" : `${districtNum}th`;
  return `https://ballotpedia.org/${bpState}%27s_${distStr}_Congressional_District_election,_${year}`;
}

/**
 * Read the district number from a GeoJSON feature's properties.
 * Checks CD119FP, CD118FP, cd118fp in order (handles Census schema drift).
 * Returns 0 for missing or non-numeric values — this is the at-large sentinel.
 * @param {object} props GeoJSON feature properties object
 * @returns {number}
 */
export function districtNumFromProps(props) {
  if (!props) return 0;
  // Use "in" checks so that a legitimate "00" (at-large) is read as 0,
  // not mistakenly falling through to the next field.
  let raw;
  if ("CD119FP" in props) raw = props.CD119FP;
  else if ("CD118FP" in props) raw = props.CD118FP;
  else if ("cd118fp" in props) raw = props.cd118fp;
  else return 0;
  const n = parseInt(raw, 10);
  return Number.isFinite(n) ? n : 0;
}
