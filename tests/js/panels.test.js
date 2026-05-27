// Unit tests for pure panel HTML generators in js/panels.js
import { describe, it, expect } from "vitest";
import {
  welcomePanelHtml,
  memberCardHtml,
  senatorsHtml,
  statePanelHtml,
  districtPanelHtml,
  stateLegDistrictPanelHtml,
} from "../../js/panels.js";

describe("welcomePanelHtml", () => {
  const html = welcomePanelHtml();
  it("contains the welcome heading", () => {
    expect(html).toContain("Welcome");
  });
  it("contains instructional list items", () => {
    expect(html).toContain("<li>");
    expect(html).toContain("<ul>");
  });
  it("mentions clicking a state", () => {
    expect(html.toLowerCase()).toContain("click");
    expect(html.toLowerCase()).toContain("state");
  });
});

describe("memberCardHtml", () => {
  it("renders a normal rep with party class", () => {
    const html = memberCardHtml({
      name: "Jane Smith",
      party: "Republican",
      url: "https://example.com",
    });
    expect(html).toContain("Jane Smith");
    expect(html).toContain("party-r");
    expect(html).toContain("https://example.com");
  });
  it("renders a Democrat with party-d class", () => {
    const html = memberCardHtml({ name: "X", party: "Democrat", url: "" });
    expect(html).toContain("party-d");
  });
  it("renders vacant seats with reason", () => {
    const html = memberCardHtml({
      vacant: true,
      vacancy_reason: "Rep. X died",
    });
    expect(html).toContain("Seat Vacant");
    expect(html).toContain("Rep. X died");
  });
  it("falls back to # when url is empty", () => {
    const html = memberCardHtml({ name: "X", party: "D", url: "" });
    expect(html).toContain('href="#"');
  });
  it("returns empty string for null member", () => {
    expect(memberCardHtml(null)).toBe("");
  });
});

describe("senatorsHtml", () => {
  it("renders a card per senator", () => {
    const html = senatorsHtml([
      { name: "A", party: "Democrat", url: "" },
      { name: "B", party: "Republican", url: "" },
    ]);
    expect(html).toContain("A");
    expect(html).toContain("B");
    expect((html.match(/member-card/g) || []).length).toBe(2);
  });
  it("falls back to 'No data available' for empty list", () => {
    expect(senatorsHtml([])).toContain("No data available");
  });
  it("falls back to 'No data available' for null", () => {
    expect(senatorsHtml(null)).toContain("No data available");
  });
});

describe("statePanelHtml", () => {
  const meta = { voter_reg: { url: "https://reg.example", name: "CA Reg" } };
  const senators = [{ name: "Alice", party: "Democrat", url: "https://a.example" }];

  it("contains the state name", () => {
    const html = statePanelHtml("CA", "California", meta, senators, "current");
    expect(html).toContain("California");
  });
  it("renders the federal toggle buttons (Current + 2026 Expected)", () => {
    const html = statePanelHtml("CA", "California", meta, senators, "current");
    expect(html).toMatch(/data-view="current"[^>]*>\s*Current/);
    expect(html).toMatch(/data-view="2026"[^>]*>\s*2026 Expected/);
  });
  it("marks the current view as active", () => {
    const html = statePanelHtml("CA", "California", meta, senators, "current");
    expect(html).toMatch(/class="active"[^>]*data-action="switch-view"[^>]*data-view="current"/);
  });
  it("marks 2026 view as active when viewMode=2026", () => {
    const html = statePanelHtml("CA", "California", meta, senators, "2026");
    expect(html).toMatch(/class="active"[^>]*data-action="switch-view"[^>]*data-view="2026"/);
  });
  it("renders the state-legislature toggle for known states", () => {
    const html = statePanelHtml("VA", "Virginia", meta, senators, "current");
    expect(html).toContain('data-view="state_upper"');
    expect(html).toContain('data-view="state_lower"');
    expect(html).toContain("Senate of Virginia");
    expect(html).toContain("Virginia House of Delegates");
  });
  it("hides the lower-chamber button for unicameral Nebraska", () => {
    const html = statePanelHtml("NE", "Nebraska", meta, senators, "current");
    expect(html).toContain('data-view="state_upper"');
    expect(html).not.toContain('data-view="state_lower"');
    expect(html).toContain("Nebraska Legislature");
  });
  it("hides the entire state-legislature toggle for states without meta (DC)", () => {
    const html = statePanelHtml("DC", "District of Columbia", meta, senators, "current");
    expect(html).not.toContain('data-view="state_upper"');
    expect(html).not.toContain('data-view="state_lower"');
    expect(html).not.toContain("State Legislature");
  });
  it("marks state_upper as active when viewMode=state_upper", () => {
    const html = statePanelHtml("VA", "Virginia", meta, senators, "state_upper");
    expect(html).toMatch(/class="active"[^>]*data-action="switch-view"[^>]*data-view="state_upper"/);
  });
  it("references the state's body name (e.g. Virginia General Assembly)", () => {
    const html = statePanelHtml("VA", "Virginia", meta, senators, "current");
    expect(html).toContain("Virginia General Assembly");
  });
  it("includes the voter registration link", () => {
    const html = statePanelHtml("CA", "California", meta, senators, "current");
    expect(html).toContain("https://reg.example");
    expect(html).toContain("CA Reg");
  });
  it("falls back to # when no registration url", () => {
    const html = statePanelHtml("CA", "California", {}, senators, "current");
    expect(html).toContain('href="#"');
  });
  it("uses data-action attributes instead of inline onclick", () => {
    const html = statePanelHtml("CA", "California", meta, senators, "current");
    expect(html).not.toContain("onclick");
    expect(html).toContain('data-action="reset-national"');
    expect(html).toContain('data-action="switch-view"');
  });
  it("includes the back-to-national button", () => {
    const html = statePanelHtml("CA", "California", meta, senators, "current");
    expect(html).toContain("National View");
  });
});

describe("districtPanelHtml", () => {
  const reg = { url: "https://ca-reg.example", name: "CA Voter Registration" };

  it("renders the rep when present", () => {
    const rep = { name: "Jane Rep", party: "Democrat", url: "https://j.example" };
    const html = districtPanelHtml("CA", 5, "District 5", rep, reg, "current");
    expect(html).toContain("Jane Rep");
  });
  it("renders a vacant seat card for vacant reps", () => {
    const rep = { vacant: true, vacancy_reason: "Resigned" };
    const html = districtPanelHtml("NJ", 11, "District 11", rep, reg, "current");
    expect(html).toContain("Seat Vacant");
    expect(html).toContain("Resigned");
  });
  it("shows 'No data found' when rep is null", () => {
    const html = districtPanelHtml("WY", 0, "At-Large", null, reg, "current");
    expect(html).toContain("No data found");
  });
  it("includes a Ballotpedia URL", () => {
    const html = districtPanelHtml("CA", 1, "District 1", null, reg, "current");
    expect(html).toContain("ballotpedia.org");
  });
  it("labels '119th Congress boundaries' for current view", () => {
    const html = districtPanelHtml("CA", 1, "District 1", null, reg, "current");
    expect(html).toContain("119th Congress boundaries");
  });
  it("labels '2026 expected boundaries' for 2026 view", () => {
    const html = districtPanelHtml("CA", 1, "District 1", null, reg, "2026");
    expect(html).toContain("2026 expected boundaries");
  });
  it("back button references the state abbr", () => {
    const html = districtPanelHtml("CA", 1, "District 1", null, reg, "current");
    expect(html).toContain("CA Overview");
    expect(html).toMatch(/data-action="back-to-state"[^>]*data-abbr="CA"/);
  });
  it("renders voter registration link", () => {
    const html = districtPanelHtml("CA", 1, "District 1", null, reg, "current");
    expect(html).toContain("https://ca-reg.example");
  });
  it("uses data-action, not inline onclick", () => {
    const html = districtPanelHtml("CA", 1, "District 1", null, reg, "current");
    expect(html).not.toContain("onclick");
  });
});

describe("stateLegDistrictPanelHtml", () => {
  const reg = { url: "https://va-reg.example", name: "Virginia Voter Registration" };
  const memberD = { name: "Aaron Rouse", party: "Democratic" };

  it("uses 'Senator' prefix for upper-chamber members", () => {
    const html = stateLegDistrictPanelHtml("VA", "upper", "22", memberD, reg);
    expect(html).toContain("Senator Aaron Rouse");
  });
  it("uses 'Delegate' prefix for VA lower-chamber members", () => {
    const html = stateLegDistrictPanelHtml("VA", "lower", "5",
      { name: "Adele McClure", party: "Democratic" }, reg);
    expect(html).toContain("Delegate Adele McClure");
  });
  it("uses 'Assemblymember' prefix for CA lower-chamber members", () => {
    const html = stateLegDistrictPanelHtml("CA", "lower", "10",
      { name: "Jane Doe", party: "Democratic" }, reg);
    expect(html).toContain("Assemblymember Jane Doe");
  });
  it("references the chamber by its state-correct display name", () => {
    const html = stateLegDistrictPanelHtml("VA", "upper", "22", memberD, reg);
    expect(html).toContain("Senate of Virginia");
    expect(html).toContain("District 22");
  });
  it("references the body name for Virginia", () => {
    const html = stateLegDistrictPanelHtml("VA", "upper", "22", memberD, reg);
    expect(html).toContain("Virginia General Assembly");
  });
  it("includes a Ballotpedia district URL with the correct slug", () => {
    const html = stateLegDistrictPanelHtml("VA", "lower", "5",
      { name: "X", party: "Democratic" }, reg);
    expect(html).toContain("https://ballotpedia.org/Virginia_House_of_Delegates_District_5");
  });
  it("renders a fallback when no legislator is on record", () => {
    const html = stateLegDistrictPanelHtml("VA", "upper", "22", null, reg);
    expect(html).toContain("No legislator on record");
  });
  it("includes a back-to-state button", () => {
    const html = stateLegDistrictPanelHtml("VA", "upper", "22", memberD, reg);
    expect(html).toContain('data-action="back-to-state"');
    expect(html).toContain('data-abbr="VA"');
  });
  it("includes the voter registration link", () => {
    const html = stateLegDistrictPanelHtml("VA", "upper", "22", memberD, reg);
    expect(html).toContain("https://va-reg.example");
  });
  it("uses data-action attributes, no inline onclick", () => {
    const html = stateLegDistrictPanelHtml("VA", "upper", "22", memberD, reg);
    expect(html).not.toContain("onclick");
  });
  it("degrades gracefully for states with no legislature meta", () => {
    const html = stateLegDistrictPanelHtml("DC", "upper", "1", null, reg);
    expect(html).toContain("District 1");
    // Should still produce a valid back button
    expect(html).toContain('data-action="back-to-state"');
  });
});
