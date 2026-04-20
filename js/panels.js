// Pure HTML-string generators for the sidebar panels.
// These functions never touch `document`. They take data as arguments
// and return HTML strings. The caller (main.js) writes the result
// into #sidebar-content.
//
// Button interactions use `data-action="..."` attributes rather than
// inline `onclick="..."` so that the returned HTML does not depend
// on any globally-exposed functions. main.js wires up a single
// delegated event listener.

import { partyClass, ballotpediaUrl } from "./utils.js";

/**
 * The welcome/instructions panel shown before any state is selected.
 */
export function welcomePanelHtml() {
  return `
    <div id="panel-welcome">
      <h2>Welcome</h2>
      <div class="welcome">
        <p>Click any state to explore voting information and congressional districts.</p>
        <ul>
          <li>States are colored by 2024 Presidential Election result</li>
          <li>Click a state to zoom in and see congressional districts</li>
          <li>Click a district to see your representative</li>
        </ul>
      </div>
    </div>`;
}

/**
 * Render a single member card (senator or representative).
 * @param {object} member { name, party, url, vacant?, vacancy_reason? }
 */
export function memberCardHtml(member) {
  if (!member) return "";
  if (member.vacant) {
    return `
      <div class="member-card" style="border-left:3px solid #e67e22;">
        <strong style="color:#e67e22;">Seat Vacant</strong><br/>
        <span style="font-size:.8rem;color:#666;">${member.vacancy_reason || ""}</span>
      </div>`;
  }
  const cls = partyClass(member.party);
  const href = member.url || "#";
  return `
      <div class="member-card">
        <a href="${href}" target="_blank" rel="noopener">${member.name}</a><br/>
        <span class="${cls}">${member.party || ""}</span>
      </div>`;
}

/**
 * Render the senators list for a state (or a fallback message).
 * @param {Array} senators
 */
export function senatorsHtml(senators) {
  if (!senators || senators.length === 0) {
    return "<p style='color:#888;font-size:.82rem'>No data available.</p>";
  }
  return senators.map(memberCardHtml).join("");
}

/**
 * The full state-overview panel.
 * @param {string} abbr
 * @param {string} stateName
 * @param {object} meta      { voter_reg: { url, name } }
 * @param {Array}  senators  array of member objects
 * @param {string} viewMode  "current" | "2026"
 */
export function statePanelHtml(abbr, stateName, meta, senators, viewMode) {
  const reg = (meta && meta.voter_reg) || {};
  const currentActive = viewMode === "current" ? "active" : "";
  const futureActive = viewMode === "2026" ? "active" : "";

  return `
    <button class="back-btn" data-action="reset-national">&#8592; National View</button>
    <h2>${stateName}</h2>

    <div class="view-toggle">
      <button data-mode="current" class="${currentActive}"
              data-action="switch-view" data-view="current">Current Districts</button>
      <button data-mode="2026" class="${futureActive}"
              data-action="switch-view" data-view="2026">2026 Expected</button>
    </div>

    <h3>Register to Vote</h3>
    <div class="info-section">
      <a class="reg-link" href="${reg.url || "#"}" target="_blank" rel="noopener">
        ${reg.name || stateName + " Voter Registration"}
      </a>
    </div>

    <h3>U.S. Senators</h3>
    <div class="info-section">${senatorsHtml(senators)}</div>

    <h3>U.S. Representatives</h3>
    <div class="info-section">
      <p style="color:#555;font-size:.83rem;">
        Click a congressional district on the map to see the representative for that district.
      </p>
    </div>
  `;
}

/**
 * The district-detail panel.
 * @param {string} stateAbbr
 * @param {number} districtNum
 * @param {string} districtLabel
 * @param {object|null} rep   member object or null
 * @param {object} regLink    { url, name }
 * @param {string} viewMode   "current" | "2026"
 */
export function districtPanelHtml(stateAbbr, districtNum, districtLabel, rep, regLink, viewMode) {
  const reg = regLink || {};
  const repHtml = rep
    ? memberCardHtml(rep)
    : "<p style='color:#888;font-size:.82rem'>No data found for this district.</p>";
  const boundaries = viewMode === "2026"
    ? "2026 expected boundaries"
    : "119th Congress boundaries";
  const bpUrl = ballotpediaUrl(stateAbbr, districtNum, 2026);

  return `
    <button class="back-btn" data-action="back-to-state" data-abbr="${stateAbbr}">&#8592; ${stateAbbr} Overview</button>
    <h2>${districtLabel}</h2>
    <p style="font-size:.78rem;color:#888;margin-bottom:8px;">${stateAbbr} &mdash; ${boundaries}</p>

    <h3>Current Representative</h3>
    <div class="info-section">${repHtml}</div>

    <h3>2026 Midterm Election</h3>
    <div class="info-section">
      <a class="ballotpedia-link" href="${bpUrl}" target="_blank" rel="noopener">
        View 2026 Candidates on Ballotpedia
      </a>
    </div>

    <h3>Register to Vote</h3>
    <div class="info-section">
      <a class="reg-link" href="${reg.url || "#"}" target="_blank" rel="noopener">
        ${reg.name || stateAbbr + " Voter Registration"}
      </a>
    </div>
  `;
}
