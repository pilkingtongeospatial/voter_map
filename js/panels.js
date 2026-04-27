// Pure HTML-string generators for the sidebar panels.
// These functions never touch `document`. They take data as arguments
// and return HTML strings. The caller (main.js) writes the result
// into #sidebar-content.
//
// Button interactions use `data-action="..."` attributes rather than
// inline `onclick="..."` so that the returned HTML does not depend
// on any globally-exposed functions. main.js wires up a single
// delegated event listener.

import {
  partyClass,
  ballotpediaUrl,
  stateLegMeta,
  hasLowerChamber,
  chamberDisplayName,
  memberTitle,
  stateLegBallotpediaUrl,
} from "./utils.js";

/**
 * The welcome/instructions panel shown before any state is selected.
 */
export function welcomePanelHtml() {
  return `
    <div id="panel-welcome">
      <h2>Welcome</h2>
      <div class="welcome">
        <p>Click any state to explore voting information and legislative districts.</p>
        <ul>
          <li>States are colored by 2024 Presidential Election result</li>
          <li>Click a state to zoom in, then toggle between federal and state legislative districts</li>
          <li>Click a district to see the elected representative</li>
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
 * Render the federal + state-legislature view-mode toggle buttons.
 * Returns "" if the state has no STATE_LEGISLATURE_META entry AND no
 * federal districts (shouldn't happen for the 50 states + DC).
 *
 * Federal toggle is always shown. State toggle is shown only when the
 * state has STATE_LEGISLATURE_META; for unicameral Nebraska, only the
 * upper-chamber button appears (and spans full width).
 *
 * @param {string} abbr
 * @param {string} viewMode  "current" | "2026" | "state_upper" | "state_lower"
 */
function viewToggleHtml(abbr, viewMode) {
  const cls = (mode) => viewMode === mode ? "active" : "";
  const legMeta = stateLegMeta(abbr);

  let html = `
    <div class="view-toggle-section">
      <span class="view-toggle-label">Federal Districts</span>
      <div class="view-toggle">
        <button class="${cls("current")}" data-action="switch-view" data-view="current">Current</button>
        <button class="${cls("2026")}" data-action="switch-view" data-view="2026">2026 Expected</button>
      </div>
    </div>`;

  if (legMeta) {
    const upperLabel = legMeta.upper_chamber || "State Senate";
    html += `
    <div class="view-toggle-section">
      <span class="view-toggle-label">State Legislature</span>
      <div class="view-toggle">
        <button class="${cls("state_upper")}" data-action="switch-view" data-view="state_upper">${upperLabel}</button>`;
    if (hasLowerChamber(abbr)) {
      html += `
        <button class="${cls("state_lower")}" data-action="switch-view" data-view="state_lower">${legMeta.lower_chamber}</button>`;
    }
    html += `
      </div>
    </div>`;
  }

  return html;
}

/**
 * The full state-overview panel.
 * @param {string} abbr
 * @param {string} stateName
 * @param {object} meta      { voter_reg: { url, name } }
 * @param {Array}  senators  array of member objects
 * @param {string} viewMode  "current" | "2026" | "state_upper" | "state_lower"
 */
export function statePanelHtml(abbr, stateName, meta, senators, viewMode) {
  const reg = (meta && meta.voter_reg) || {};
  const isStateMode = viewMode === "state_upper" || viewMode === "state_lower";
  const legMeta = stateLegMeta(abbr);

  // Adjust the click prompt based on which layer is active
  let clickHint;
  if (isStateMode && legMeta) {
    const chamber = viewMode === "state_upper" ? "upper" : "lower";
    const chamberName = chamberDisplayName(abbr, chamber) || "state legislative";
    clickHint = `Click a ${chamberName} district on the map to see the legislator for that district.`;
  } else {
    clickHint = "Click a congressional district on the map to see the representative for that district.";
  }

  const stateLegHeading = legMeta
    ? `<h3>${legMeta.body}</h3>
       <div class="info-section">
         <p style="color:#555;font-size:.83rem;">
           Use the State Legislature toggle above to view districts for the
           ${legMeta.upper_chamber}${legMeta.lower_chamber ? ` and ${legMeta.lower_chamber}` : ""}.
         </p>
       </div>`
    : "";

  return `
    <button class="back-btn" data-action="reset-national">&#8592; National View</button>
    <h2>${stateName}</h2>

    ${viewToggleHtml(abbr, viewMode)}

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
      <p style="color:#555;font-size:.83rem;">${clickHint}</p>
    </div>

    ${stateLegHeading}
  `;
}

/**
 * The federal congressional-district detail panel.
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

/**
 * Render a single state-legislator card. Like memberCardHtml but with a
 * member-title prefix ("Delegate Jane Doe", "Assemblymember John Smith").
 * @param {string} title    e.g. "Senator", "Delegate"
 * @param {object|null} member  { name, party }
 */
function stateLegislatorCardHtml(title, member) {
  if (!member) {
    return "<p style='color:#888;font-size:.82rem'>No legislator on record for this district.</p>";
  }
  const cls = partyClass(member.party);
  const prefix = title ? `${title} ` : "";
  return `
      <div class="member-card">
        <strong>${prefix}${member.name}</strong><br/>
        <span class="${cls}">${member.party || ""}</span>
      </div>`;
}

/**
 * The state-legislative-district detail panel.
 * @param {string} stateAbbr
 * @param {"upper"|"lower"} chamber
 * @param {string} district             e.g. "5", "12B"
 * @param {object|null} legislator      { name, party } or null
 * @param {object} regLink              { url, name }
 */
export function stateLegDistrictPanelHtml(stateAbbr, chamber, district, legislator, regLink) {
  const reg = regLink || {};
  const meta = stateLegMeta(stateAbbr);
  if (!meta) {
    // Defensive — should not normally hit this for the 50 states.
    return `
      <button class="back-btn" data-action="back-to-state" data-abbr="${stateAbbr}">&#8592; ${stateAbbr} Overview</button>
      <h2>District ${district}</h2>
      <p style='color:#888;font-size:.82rem'>No legislative metadata available for this state.</p>`;
  }
  const chamberName = chamberDisplayName(stateAbbr, chamber);
  const title = memberTitle(stateAbbr, chamber);
  const bpUrl = stateLegBallotpediaUrl(stateAbbr, chamber, district);
  const bodyName = meta.body;
  const bodyUrl = `https://ballotpedia.org/${meta.body_url_slug}`;
  const districtHeading = `${chamberName}, District ${district}`;

  return `
    <button class="back-btn" data-action="back-to-state" data-abbr="${stateAbbr}">&#8592; ${stateAbbr} Overview</button>
    <h2>${districtHeading}</h2>
    <p style="font-size:.78rem;color:#888;margin-bottom:8px;">
      <a href="${bodyUrl}" target="_blank" rel="noopener" style="color:#666;">${bodyName}</a>
    </p>

    <h3>Current ${title || "Legislator"}</h3>
    <div class="info-section">${stateLegislatorCardHtml(title, legislator)}</div>

    <h3>District Information</h3>
    <div class="info-section">
      <a class="ballotpedia-link" href="${bpUrl}" target="_blank" rel="noopener">
        View District on Ballotpedia
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
