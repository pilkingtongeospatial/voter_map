"""Unit tests for the pure transformation functions in scripts/transforms.py."""

from copy import deepcopy

import pytest

from transforms import (
    annotate_states,
    apply_manual_overrides,
    build_state_meta,
    flatten_legislators,
    flatten_state_legislators,
    merge_cd_geojson,
    normalize_redistricted_feature,
)


# ── annotate_states ───────────────────────────────────────────────────────────

def _state_feat(name):
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"name": name}, "geometry": None}
        ],
    }


def test_annotate_known_state():
    name_to_abbr = {"California": "CA"}
    election = {"CA": "D"}
    out = annotate_states(_state_feat("California"), name_to_abbr, election)
    props = out["features"][0]["properties"]
    assert props["abbr"] == "CA"
    assert props["party"] == "D"


def test_annotate_unknown_state_no_error():
    out = annotate_states(_state_feat("Atlantis"), {"California": "CA"}, {"CA": "D"})
    props = out["features"][0]["properties"]
    assert props["abbr"] == ""
    assert props["party"] == ""


def test_annotate_no_mutation():
    raw = _state_feat("California")
    before = deepcopy(raw)
    annotate_states(raw, {"California": "CA"}, {"CA": "D"})
    assert raw == before


def test_annotate_empty_features():
    out = annotate_states({"type": "FeatureCollection", "features": []}, {}, {})
    assert out["features"] == []


# ── normalize_redistricted_feature ────────────────────────────────────────────

def test_normalize_basic():
    feat = {
        "type": "Feature",
        "properties": {"DISTRICT": "5", "ST": "06", "DIST_NAME": "District 5"},
        "geometry": None,
    }
    out = normalize_redistricted_feature(feat, "06")
    p = out["properties"]
    assert p["CD119FP"] == "05"
    assert p["STATEFP"] == "06"
    assert p["GEOID"] == "0605"
    assert p["CDSESSN"] == "119"
    assert p["SOURCE"] == "redistricting_2025"
    assert p["NAMELSAD"] == "District 5"


def test_normalize_zero_pads_to_two_digits():
    feat = {"type": "Feature", "properties": {"DISTRICT": "1"}, "geometry": None}
    out = normalize_redistricted_feature(feat, "06")
    assert out["properties"]["CD119FP"] == "01"


def test_normalize_district_zero():
    feat = {"type": "Feature", "properties": {"DISTRICT": "0"}, "geometry": None}
    out = normalize_redistricted_feature(feat, "06")
    assert out["properties"]["CD119FP"] == "00"


def test_normalize_uses_fips_when_st_missing():
    feat = {"type": "Feature", "properties": {"DISTRICT": "3"}, "geometry": None}
    out = normalize_redistricted_feature(feat, "48")
    assert out["properties"]["STATEFP"] == "48"


def test_normalize_default_namelsad():
    feat = {"type": "Feature", "properties": {"DISTRICT": "7"}, "geometry": None}
    out = normalize_redistricted_feature(feat, "06")
    assert out["properties"]["NAMELSAD"] == "Congressional District 7"


def test_normalize_no_mutation():
    feat = {
        "type": "Feature",
        "properties": {"DISTRICT": "5", "ST": "06", "DIST_NAME": "District 5"},
        "geometry": None,
    }
    before = deepcopy(feat)
    normalize_redistricted_feature(feat, "06")
    assert feat == before


# ── merge_cd_geojson ──────────────────────────────────────────────────────────

def _cd_feat(statefp, cd):
    return {"type": "Feature", "properties": {"STATEFP": statefp, "CD119FP": cd}, "geometry": None}


def test_merge_removes_redistricted():
    base = {"features": [_cd_feat("06", "01"), _cd_feat("48", "02"), _cd_feat("01", "01")]}
    out = merge_cd_geojson(base, {"06", "48"}, [])
    remaining_fips = [f["properties"]["STATEFP"] for f in out["features"]]
    assert remaining_fips == ["01"]


def test_merge_appends_new_features():
    base = {"features": [_cd_feat("06", "01")]}
    new = [_cd_feat("06", "01"), _cd_feat("06", "02")]
    out = merge_cd_geojson(base, {"06"}, new)
    assert len(out["features"]) == 2
    assert out["features"] == new


def test_merge_empty_new_keeps_all_non_redistricted():
    base = {"features": [_cd_feat("01", "01"), _cd_feat("02", "01")]}
    out = merge_cd_geojson(base, set(), [])
    assert len(out["features"]) == 2


def test_merge_returns_feature_collection():
    out = merge_cd_geojson({"features": []}, set(), [])
    assert out["type"] == "FeatureCollection"


# ── flatten_legislators ───────────────────────────────────────────────────────

def _leg(*, name=None, terms=None, first=None, last=None):
    n = {}
    if name is not None:
        n["official_full"] = name
    if first is not None:
        n["first"] = first
    if last is not None:
        n["last"] = last
    return {"name": n, "terms": terms or []}


def test_flatten_senator():
    data = [_leg(name="Jane Smith", terms=[{"type": "sen", "state": "CA", "party": "Democrat", "url": "u"}])]
    out = flatten_legislators(data)
    assert out["CA"]["senators"] == [{"name": "Jane Smith", "party": "Democrat", "url": "u"}]


def test_flatten_rep_with_district():
    data = [_leg(name="Bob", terms=[{"type": "rep", "state": "TX", "district": 5, "party": "R", "url": ""}])]
    out = flatten_legislators(data)
    assert "5" in out["TX"]["representatives"]
    assert out["TX"]["representatives"]["5"]["name"] == "Bob"


def test_flatten_rep_no_district_becomes_zero():
    data = [_leg(name="A", terms=[{"type": "rep", "state": "AK", "party": "R"}])]
    out = flatten_legislators(data)
    assert "0" in out["AK"]["representatives"]


def test_flatten_skips_empty_terms():
    data = [_leg(name="Nobody", terms=[])]
    out = flatten_legislators(data)
    assert out == {}


def test_flatten_name_fallback_to_first_last():
    data = [_leg(first="John", last="Doe", terms=[{"type": "sen", "state": "NY", "party": "D"}])]
    out = flatten_legislators(data)
    assert out["NY"]["senators"][0]["name"] == "John Doe"


def test_flatten_url_missing_becomes_empty_string():
    data = [_leg(name="X", terms=[{"type": "sen", "state": "CA", "party": "D"}])]
    out = flatten_legislators(data)
    assert out["CA"]["senators"][0]["url"] == ""


def test_flatten_handles_none_input():
    assert flatten_legislators(None) == {}


# ── apply_manual_overrides ────────────────────────────────────────────────────

def test_override_fills_missing_seat():
    by_state = {}
    overrides = {("CA", "1"): {"name": "Vacant", "party": "", "url": ""}}
    out, n = apply_manual_overrides(by_state, overrides)
    assert n == 1
    assert out["CA"]["representatives"]["1"]["name"] == "Vacant"


def test_override_skips_filled_seat():
    by_state = {
        "CA": {
            "senators": [],
            "representatives": {"1": {"name": "Real Rep", "party": "D", "url": ""}},
        }
    }
    overrides = {("CA", "1"): {"name": "Override", "party": "", "url": ""}}
    out, n = apply_manual_overrides(by_state, overrides)
    assert n == 0
    assert out["CA"]["representatives"]["1"]["name"] == "Real Rep"


def test_override_count_matches_applied():
    by_state = {"CA": {"senators": [], "representatives": {"1": {"name": "R"}}}}
    overrides = {
        ("CA", "1"): {"name": "A"},   # skipped
        ("CA", "2"): {"name": "B"},   # applied
        ("NJ", "11"): {"name": "C"},  # applied (new state)
    }
    _, n = apply_manual_overrides(by_state, overrides)
    assert n == 2


def test_override_no_mutation():
    by_state = {"CA": {"senators": [], "representatives": {}}}
    before = deepcopy(by_state)
    apply_manual_overrides(by_state, {("CA", "1"): {"name": "V"}})
    assert by_state == before


# ── build_state_meta ──────────────────────────────────────────────────────────

def test_build_meta_basic():
    voter_reg = {"CA": {"url": "x", "name": "CA Reg"}, "TX": {"url": "y", "name": "TX Reg"}}
    election = {"CA": "D", "TX": "R"}
    out = build_state_meta(voter_reg, election)
    assert out["CA"] == {"voter_reg": {"url": "x", "name": "CA Reg"}, "party": "D"}
    assert out["TX"] == {"voter_reg": {"url": "y", "name": "TX Reg"}, "party": "R"}


def test_build_meta_unknown_party_becomes_empty():
    voter_reg = {"PR": {"url": "u", "name": "PR Reg"}}
    out = build_state_meta(voter_reg, {})
    assert out["PR"]["party"] == ""


def test_build_meta_only_voter_reg_abbrs():
    voter_reg = {"CA": {"url": "x", "name": "y"}}
    election = {"CA": "D", "TX": "R"}  # TX should NOT appear in output
    out = build_state_meta(voter_reg, election)
    assert set(out.keys()) == {"CA"}


# ── flatten_state_legislators ────────────────────────────────────────────────

def _row(state, chamber, district, name="X", party="Democratic"):
    return {
        "state": state, "current_chamber": chamber,
        "current_district": district, "name": name, "current_party": party,
    }


def test_flatten_sl_basic_upper_and_lower():
    rows = [
        _row("VA", "upper", "5",  name="Jane Doe"),
        _row("VA", "lower", "12", name="John Smith", party="Republican"),
    ]
    out = flatten_state_legislators(rows)
    assert out["VA"]["upper"]["5"] == {"name": "Jane Doe", "party": "Democratic"}
    assert out["VA"]["lower"]["12"] == {"name": "John Smith", "party": "Republican"}


def test_flatten_sl_nebraska_unicameral_remapped_to_upper():
    rows = [
        _row("NE", "legislature", "13", name="Ashlei Spivey", party="Nonpartisan"),
    ]
    out = flatten_state_legislators(rows)
    assert "upper" in out["NE"]
    assert out["NE"]["upper"]["13"] == {"name": "Ashlei Spivey", "party": "Nonpartisan"}
    assert out["NE"].get("lower", {}) == {}


def test_flatten_sl_skips_rows_with_missing_fields():
    rows = [
        _row("VA", "upper", "", name="No district"),
        _row("VA", "upper", "5", name=""),
        _row("VA", "", "5", name="No chamber"),
        {"name": "no state", "current_chamber": "upper", "current_district": "5"},
        _row("VA", "upper", "7", name="Real"),
    ]
    out = flatten_state_legislators(rows)
    assert list(out.get("VA", {}).get("upper", {}).keys()) == ["7"]


def test_flatten_sl_unknown_chamber_skipped():
    rows = [
        _row("VA", "council", "5", name="Council member"),
        _row("VA", "upper", "5", name="Senator"),
    ]
    out = flatten_state_legislators(rows)
    assert list(out["VA"]["upper"].keys()) == ["5"]
    assert "council" not in out["VA"]


def test_flatten_sl_multi_member_district_joins_names():
    rows = [
        _row("ND", "lower", "5", name="Alice", party="Republican"),
        _row("ND", "lower", "5", name="Bob", party="Republican"),
    ]
    out = flatten_state_legislators(rows)
    assert out["ND"]["lower"]["5"]["name"] == "Alice / Bob"


def test_flatten_sl_party_default_when_blank():
    rows = [_row("VA", "upper", "5", name="X", party="")]
    out = flatten_state_legislators(rows)
    assert out["VA"]["upper"]["5"]["party"] == "Unknown"


def test_flatten_sl_empty_input():
    assert flatten_state_legislators([]) == {}
    assert flatten_state_legislators(None) == {}


def test_flatten_sl_no_mutation():
    rows = [_row("VA", "upper", "5", name="X")]
    before = deepcopy(rows)
    flatten_state_legislators(rows)
    assert rows == before
