// Unit tests for pure utility functions in js/utils.js
import { describe, it, expect } from "vitest";
import {
  partyClass,
  stateStyle,
  abbrToFips,
  fipsToAbbr,
  ballotpediaUrl,
  districtNumFromProps,
  stateLegMeta,
  hasLowerChamber,
  chamberDisplayName,
  memberTitle,
  stateLegDistrictFromProps,
  stateLegBallotpediaUrl,
} from "../../js/utils.js";

describe("partyClass", () => {
  it("returns party-r for Republican", () => {
    expect(partyClass("Republican")).toBe("party-r");
  });
  it("is case-insensitive", () => {
    expect(partyClass("REPUBLICAN")).toBe("party-r");
    expect(partyClass("democrat")).toBe("party-d");
  });
  it("returns party-d for Democrat", () => {
    expect(partyClass("Democrat")).toBe("party-d");
  });
  it("returns party-i for Independent", () => {
    expect(partyClass("Independent")).toBe("party-i");
  });
  it("returns party-i for any unknown party", () => {
    expect(partyClass("Libertarian")).toBe("party-i");
  });
  it("returns empty string for null", () => {
    expect(partyClass(null)).toBe("");
  });
  it("returns empty string for undefined", () => {
    expect(partyClass(undefined)).toBe("");
  });
  it("returns empty string for empty string", () => {
    expect(partyClass("")).toBe("");
  });
});

describe("stateStyle", () => {
  it("fills R with red", () => {
    const s = stateStyle({ properties: { party: "R" } });
    expect(s.fillColor).toBe("#c0392b");
  });
  it("fills D with blue", () => {
    const s = stateStyle({ properties: { party: "D" } });
    expect(s.fillColor).toBe("#2471a3");
  });
  it("fills unknown with grey", () => {
    expect(stateStyle({ properties: { party: "X" } }).fillColor).toBe("#888");
    expect(stateStyle({ properties: {} }).fillColor).toBe("#888");
  });
  it("returns fixed style properties", () => {
    const s = stateStyle({ properties: { party: "R" } });
    expect(s.fillOpacity).toBe(0.55);
    expect(s.color).toBe("#fff");
    expect(s.weight).toBe(1.5);
    expect(s.opacity).toBe(1);
  });
  it("handles missing feature gracefully", () => {
    const s = stateStyle({});
    expect(s.fillColor).toBe("#888");
  });
});

describe("fipsToAbbr", () => {
  it("returns CA for 06", () => {
    expect(fipsToAbbr("06")).toBe("CA");
  });
  it("returns empty string for unknown FIPS", () => {
    expect(fipsToAbbr("99")).toBe("");
  });
});

describe("abbrToFips", () => {
  it("returns 06 for CA", () => {
    expect(abbrToFips("CA")).toBe("06");
  });
  it("returns null for unknown abbr", () => {
    expect(abbrToFips("XX")).toBe(null);
  });
});

describe("ballotpediaUrl", () => {
  it("uses at_Large for district 0", () => {
    const url = ballotpediaUrl("AK", 0, 2026);
    expect(url).toContain("at_Large");
  });
  it("appends 'th' for numbered districts", () => {
    const url = ballotpediaUrl("CA", 12, 2026);
    expect(url).toContain("12th");
  });
  it("includes the year", () => {
    const url = ballotpediaUrl("TX", 1, 2026);
    expect(url).toContain("2026");
  });
  it("uses the state's ballotpedia name", () => {
    // NY -> "New_York" (underscore-escaped)
    expect(ballotpediaUrl("NY", 1, 2026)).toContain("New_York");
  });
  it("falls back to abbr for unknown state", () => {
    expect(ballotpediaUrl("XX", 1, 2026)).toContain("XX");
  });
});

describe("districtNumFromProps", () => {
  it("reads CD119FP first", () => {
    expect(districtNumFromProps({ CD119FP: "05" })).toBe(5);
  });
  it("falls back to CD118FP", () => {
    expect(districtNumFromProps({ CD118FP: "03" })).toBe(3);
  });
  it("falls back to lowercase cd118fp", () => {
    expect(districtNumFromProps({ cd118fp: "07" })).toBe(7);
  });
  it("prefers CD119FP over CD118FP", () => {
    expect(districtNumFromProps({ CD119FP: "01", CD118FP: "99" })).toBe(1);
  });
  it("handles at-large '00' correctly (returns 0, not falling through)", () => {
    expect(districtNumFromProps({ CD119FP: "00", CD118FP: "05" })).toBe(0);
  });
  it("returns 0 for missing properties", () => {
    expect(districtNumFromProps({})).toBe(0);
  });
  it("returns 0 for null input", () => {
    expect(districtNumFromProps(null)).toBe(0);
  });
  it("returns 0 for non-numeric values", () => {
    expect(districtNumFromProps({ CD119FP: "ZZ" })).toBe(0);
  });
});

// ── state-legislature helpers ────────────────────────────────────────────────

describe("stateLegMeta", () => {
  it("returns the meta object for a known state", () => {
    const m = stateLegMeta("VA");
    expect(m).not.toBeNull();
    expect(m.body).toBe("Virginia General Assembly");
  });
  it("returns null for unknown / non-state codes", () => {
    expect(stateLegMeta("DC")).toBeNull();
    expect(stateLegMeta("ZZ")).toBeNull();
  });
});

describe("hasLowerChamber", () => {
  it("is true for normal bicameral states", () => {
    expect(hasLowerChamber("VA")).toBe(true);
    expect(hasLowerChamber("CA")).toBe(true);
  });
  it("is false for unicameral Nebraska", () => {
    expect(hasLowerChamber("NE")).toBe(false);
  });
  it("is false for states with no meta entry (DC, territories)", () => {
    expect(hasLowerChamber("DC")).toBe(false);
  });
});

describe("chamberDisplayName", () => {
  it("returns 'Senate of Virginia' for VA upper", () => {
    expect(chamberDisplayName("VA", "upper")).toBe("Senate of Virginia");
  });
  it("returns 'Virginia House of Delegates' for VA lower", () => {
    expect(chamberDisplayName("VA", "lower")).toBe("Virginia House of Delegates");
  });
  it("returns 'California State Assembly' for CA lower", () => {
    expect(chamberDisplayName("CA", "lower")).toBe("California State Assembly");
  });
  it("returns 'Nebraska Legislature' for NE upper", () => {
    expect(chamberDisplayName("NE", "upper")).toBe("Nebraska Legislature");
  });
  it("returns '' for NE lower (unicameral)", () => {
    expect(chamberDisplayName("NE", "lower")).toBe("");
  });
  it("returns '' for unknown state", () => {
    expect(chamberDisplayName("DC", "upper")).toBe("");
    expect(chamberDisplayName("ZZ", "upper")).toBe("");
  });
});

describe("memberTitle", () => {
  it("returns 'Senator' for upper chambers", () => {
    expect(memberTitle("VA", "upper")).toBe("Senator");
    expect(memberTitle("CA", "upper")).toBe("Senator");
  });
  it("returns 'Delegate' for VA/MD/WV lower", () => {
    expect(memberTitle("VA", "lower")).toBe("Delegate");
    expect(memberTitle("MD", "lower")).toBe("Delegate");
    expect(memberTitle("WV", "lower")).toBe("Delegate");
  });
  it("returns 'Assemblymember' for CA/NY/NV/NJ lower", () => {
    expect(memberTitle("CA", "lower")).toBe("Assemblymember");
    expect(memberTitle("NY", "lower")).toBe("Assemblymember");
    expect(memberTitle("NV", "lower")).toBe("Assemblymember");
    expect(memberTitle("NJ", "lower")).toBe("Assemblymember");
  });
  it("returns 'Representative' for typical states", () => {
    expect(memberTitle("OH", "lower")).toBe("Representative");
    expect(memberTitle("TX", "lower")).toBe("Representative");
  });
  it("returns '' for missing chambers and unknown states", () => {
    expect(memberTitle("NE", "lower")).toBe("");
    expect(memberTitle("DC", "upper")).toBe("");
  });
});

describe("stateLegDistrictFromProps", () => {
  it("prefers NAME when present", () => {
    expect(stateLegDistrictFromProps({ NAME: "5", SLDUST: "005" }, "upper")).toBe("5");
  });
  it("strips leading zeros from SLDUST when NAME is missing", () => {
    expect(stateLegDistrictFromProps({ SLDUST: "005" }, "upper")).toBe("5");
  });
  it("strips leading zeros from SLDLST for lower chamber", () => {
    expect(stateLegDistrictFromProps({ SLDLST: "012" }, "lower")).toBe("12");
  });
  it("preserves letter suffixes on multi-member districts", () => {
    expect(stateLegDistrictFromProps({ SLDLST: "012B" }, "lower")).toBe("12B");
  });
  it("returns '' on null / missing props", () => {
    expect(stateLegDistrictFromProps(null, "upper")).toBe("");
    expect(stateLegDistrictFromProps({}, "upper")).toBe("");
  });
});

describe("stateLegBallotpediaUrl", () => {
  it("builds VA upper district URL", () => {
    expect(stateLegBallotpediaUrl("VA", "upper", "5"))
      .toBe("https://ballotpedia.org/Virginia_State_Senate_District_5");
  });
  it("builds VA lower district URL with House of Delegates slug", () => {
    expect(stateLegBallotpediaUrl("VA", "lower", "12"))
      .toBe("https://ballotpedia.org/Virginia_House_of_Delegates_District_12");
  });
  it("builds CA lower URL with State Assembly slug", () => {
    expect(stateLegBallotpediaUrl("CA", "lower", "10"))
      .toBe("https://ballotpedia.org/California_State_Assembly_District_10");
  });
  it("builds NE upper URL even though body is unicameral", () => {
    expect(stateLegBallotpediaUrl("NE", "upper", "13"))
      .toBe("https://ballotpedia.org/Nebraska_State_Senate_District_13");
  });
  it("returns '#' for NE lower (no chamber)", () => {
    expect(stateLegBallotpediaUrl("NE", "lower", "1")).toBe("#");
  });
  it("returns '#' for unknown state", () => {
    expect(stateLegBallotpediaUrl("DC", "upper", "1")).toBe("#");
    expect(stateLegBallotpediaUrl("ZZ", "upper", "1")).toBe("#");
  });
});
