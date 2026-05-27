// Pure utility functions. No DOM access, no Leaflet dependency.
// Every function here is deterministic: same input → same output.

import {
  PARTY_COLOR,
  FIPS_TO_ABBR,
  ABBR_TO_FIPS,
  ABBR_TO_BALLOTPEDIA_STATE,
  STATE_LEGISLATURE_META,
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

// ── State legislature helpers ────────────────────────────────────────────────

/**
 * Look up the per-state legislature metadata, or null if absent
 * (DC, territories — they have no STATE_LEGISLATURE_META entry).
 * @param {string} stateAbbr
 * @returns {object|null}
 */
export function stateLegMeta(stateAbbr) {
  return STATE_LEGISLATURE_META[stateAbbr] || null;
}

/**
 * Whether the state has a lower chamber. False only for Nebraska (unicameral)
 * and any state with no STATE_LEGISLATURE_META entry.
 * @param {string} stateAbbr
 * @returns {boolean}
 */
export function hasLowerChamber(stateAbbr) {
  const m = STATE_LEGISLATURE_META[stateAbbr];
  return !!(m && m.lower_chamber);
}

/**
 * State-correct display name of a chamber, e.g. "Senate of Virginia" or
 * "California State Assembly". Returns "" if unknown.
 * @param {string} stateAbbr
 * @param {"upper"|"lower"} chamber
 */
export function chamberDisplayName(stateAbbr, chamber) {
  const m = STATE_LEGISLATURE_META[stateAbbr];
  if (!m) return "";
  return (chamber === "upper" ? m.upper_chamber : m.lower_chamber) || "";
}

/**
 * State-correct title prefix for a member, e.g. "Senator", "Delegate",
 * "Assemblymember". Returns "" if unknown.
 * @param {string} stateAbbr
 * @param {"upper"|"lower"} chamber
 */
export function memberTitle(stateAbbr, chamber) {
  const m = STATE_LEGISLATURE_META[stateAbbr];
  if (!m) return "";
  return (chamber === "upper" ? m.upper_member : m.lower_member) || "";
}

/**
 * Read the state-leg district number from an SLDU/SLDL feature's properties.
 * Census Cartographic Boundary files use SLDUST (upper) and SLDLST (lower);
 * the unpadded string is also exposed as NAME. Returns the trimmed string,
 * which matches OpenStates' current_district format.
 * @param {object} props GeoJSON feature properties
 * @param {"upper"|"lower"} chamber
 * @returns {string}
 */
export function stateLegDistrictFromProps(props, chamber) {
  if (!props) return "";
  // Prefer NAME (already unpadded). Fall back to SLDUST / SLDLST and strip
  // leading zeros to match OpenStates ("005" → "5", "12A" → "12A").
  if (props.NAME) return String(props.NAME).trim();
  const key = chamber === "upper" ? "SLDUST" : "SLDLST";
  const raw = props[key];
  if (raw == null) return "";
  // Strip leading zeros while preserving any letter suffix (e.g. "012B" -> "12B")
  return String(raw).replace(/^0+(?=\d)/, "").trim();
}

/**
 * Build a Ballotpedia URL for a state-leg district race.
 *   https://ballotpedia.org/<chamber_url_slug>_District_<district>
 * @param {string} stateAbbr
 * @param {"upper"|"lower"} chamber
 * @param {string|number} district
 * @returns {string} URL, or "#" if the chamber is unknown
 */
export function stateLegBallotpediaUrl(stateAbbr, chamber, district) {
  const m = STATE_LEGISLATURE_META[stateAbbr];
  if (!m) return "#";
  const slug = chamber === "upper" ? m.upper_url_slug : m.lower_url_slug;
  if (!slug) return "#";
  return `https://ballotpedia.org/${slug}_District_${district}`;
}
