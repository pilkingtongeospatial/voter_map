// Data-integrity tests for js/constants.js
import { describe, it, expect } from "vitest";
import {
  PARTY_COLOR,
  PARTY_LABEL,
  FIPS_TO_ABBR,
  ABBR_TO_FIPS,
  STATE_CENTROIDS,
  ABBR_TO_BALLOTPEDIA_STATE,
  STATE_LEGISLATURE_META,
} from "../../js/constants.js";

const ALL_50 = new Set([
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]);

describe("PARTY_COLOR", () => {
  it("has R and D keys", () => {
    expect(PARTY_COLOR.R).toBeDefined();
    expect(PARTY_COLOR.D).toBeDefined();
  });
  it("values are hex color strings", () => {
    expect(PARTY_COLOR.R).toMatch(/^#[0-9a-f]{6}$/i);
    expect(PARTY_COLOR.D).toMatch(/^#[0-9a-f]{6}$/i);
  });
});

describe("PARTY_LABEL", () => {
  it("has expected keys", () => {
    expect(PARTY_LABEL.R).toBe("Republican");
    expect(PARTY_LABEL.D).toBe("Democrat");
    expect(PARTY_LABEL.Independent).toBe("Independent");
  });
});

describe("FIPS_TO_ABBR", () => {
  it("maps 06 to CA", () => {
    expect(FIPS_TO_ABBR["06"]).toBe("CA");
  });
  it("maps 48 to TX", () => {
    expect(FIPS_TO_ABBR["48"]).toBe("TX");
  });
  it("has DC alongside the 50 states", () => {
    expect(FIPS_TO_ABBR["11"]).toBe("DC");
  });
  it("covers all 50 states", () => {
    const abbrs = new Set(Object.values(FIPS_TO_ABBR));
    for (const a of ALL_50) expect(abbrs.has(a)).toBe(true);
  });
});

describe("ABBR_TO_FIPS", () => {
  it("is the inverse of FIPS_TO_ABBR", () => {
    for (const [fips, abbr] of Object.entries(FIPS_TO_ABBR)) {
      expect(ABBR_TO_FIPS[abbr]).toBe(fips);
    }
  });
});

describe("STATE_CENTROIDS", () => {
  it("has all 50 states", () => {
    for (const abbr of ALL_50) expect(STATE_CENTROIDS[abbr]).toBeDefined();
  });
  it("each value is a [lat, lng] pair of finite numbers", () => {
    for (const [abbr, coord] of Object.entries(STATE_CENTROIDS)) {
      expect(Array.isArray(coord)).toBe(true);
      expect(coord.length).toBe(2);
      expect(Number.isFinite(coord[0])).toBe(true);
      expect(Number.isFinite(coord[1])).toBe(true);
    }
  });
});

describe("ABBR_TO_BALLOTPEDIA_STATE", () => {
  it("returns underscore-escaped state names", () => {
    expect(ABBR_TO_BALLOTPEDIA_STATE.NY).toBe("New_York");
    expect(ABBR_TO_BALLOTPEDIA_STATE.CA).toBe("California");
  });
  it("covers all 50 states", () => {
    for (const abbr of ALL_50) expect(ABBR_TO_BALLOTPEDIA_STATE[abbr]).toBeDefined();
  });
});

describe("STATE_LEGISLATURE_META", () => {
  const REQUIRED = [
    "body", "body_url_slug",
    "upper_chamber", "upper_member", "upper_url_slug",
    "lower_chamber", "lower_member", "lower_url_slug",
  ];

  it("covers all 50 states", () => {
    for (const abbr of ALL_50) expect(STATE_LEGISLATURE_META[abbr]).toBeDefined();
  });
  it("every state has all required keys", () => {
    for (const [abbr, meta] of Object.entries(STATE_LEGISLATURE_META)) {
      for (const k of REQUIRED) expect(meta).toHaveProperty(k);
    }
  });
  it("required upper-chamber strings are non-empty for every state", () => {
    for (const [abbr, meta] of Object.entries(STATE_LEGISLATURE_META)) {
      expect(meta.body, abbr).toBeTruthy();
      expect(meta.upper_chamber, abbr).toBeTruthy();
      expect(meta.upper_member, abbr).toBeTruthy();
      expect(meta.upper_url_slug, abbr).toBeTruthy();
    }
  });
  it("Nebraska is unicameral (lower_* are null)", () => {
    expect(STATE_LEGISLATURE_META.NE.lower_chamber).toBeNull();
    expect(STATE_LEGISLATURE_META.NE.lower_member).toBeNull();
    expect(STATE_LEGISLATURE_META.NE.lower_url_slug).toBeNull();
  });
  it("every other state has a lower chamber", () => {
    for (const [abbr, meta] of Object.entries(STATE_LEGISLATURE_META)) {
      if (abbr === "NE") continue;
      expect(meta.lower_chamber, abbr).toBeTruthy();
      expect(meta.lower_member, abbr).toBeTruthy();
      expect(meta.lower_url_slug, abbr).toBeTruthy();
    }
  });
  it("URL slugs are underscored (no spaces)", () => {
    for (const [abbr, meta] of Object.entries(STATE_LEGISLATURE_META)) {
      expect(meta.body_url_slug.includes(" "), abbr).toBe(false);
      expect(meta.upper_url_slug.includes(" "), abbr).toBe(false);
      if (meta.lower_url_slug) {
        expect(meta.lower_url_slug.includes(" "), abbr).toBe(false);
      }
    }
  });
  it("spot-check Virginia has correct names", () => {
    const m = STATE_LEGISLATURE_META.VA;
    expect(m.body).toBe("Virginia General Assembly");
    expect(m.upper_chamber).toBe("Senate of Virginia");
    expect(m.lower_chamber).toBe("Virginia House of Delegates");
    expect(m.lower_member).toBe("Delegate");
  });
});
