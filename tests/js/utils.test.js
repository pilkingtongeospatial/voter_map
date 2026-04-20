// Unit tests for pure utility functions in js/utils.js
import { describe, it, expect } from "vitest";
import {
  partyClass,
  stateStyle,
  abbrToFips,
  fipsToAbbr,
  ballotpediaUrl,
  districtNumFromProps,
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
