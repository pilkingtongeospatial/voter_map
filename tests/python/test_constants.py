"""Data integrity tests for scripts/constants.py."""

from constants import (
    ABBR_TO_STATE_NAME,
    ELECTION_2024,
    MANUAL_REPS,
    REDISTRICTED,
    STATE_LEGISLATURE_META,
    STATE_NAME_TO_ABBR,
    VOTER_REG,
)

# The canonical list of all 50 state abbreviations.
ALL_50 = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}


def test_election_2024_has_all_50_states():
    assert set(ELECTION_2024.keys()) == ALL_50


def test_election_2024_values_are_r_or_d():
    assert all(v in ("R", "D") for v in ELECTION_2024.values())


def test_voter_reg_has_all_50_states():
    assert set(VOTER_REG.keys()) == ALL_50


def test_voter_reg_entries_have_url_and_name():
    for abbr, entry in VOTER_REG.items():
        assert "url" in entry, f"{abbr} missing url"
        assert "name" in entry, f"{abbr} missing name"
        assert entry["url"].startswith(("http://", "https://")), f"{abbr} has non-http url"


def test_state_name_to_abbr_has_all_50_states():
    assert set(STATE_NAME_TO_ABBR.values()) == ALL_50


def test_state_name_to_abbr_no_collisions():
    # No two state names map to the same abbr
    assert len(set(STATE_NAME_TO_ABBR.values())) == len(STATE_NAME_TO_ABBR)


def test_abbr_to_state_name_is_inverse():
    # Every round-trip works
    for name, abbr in STATE_NAME_TO_ABBR.items():
        assert ABBR_TO_STATE_NAME[abbr] == name


def test_redistricted_keys_are_two_digit_fips():
    for fips in REDISTRICTED:
        assert len(fips) == 2 and fips.isdigit()


def test_redistricted_values_are_three_tuples():
    for fips, val in REDISTRICTED.items():
        assert len(val) == 3
        abbr, zip_name, url = val
        assert abbr in ALL_50
        assert zip_name.endswith(".zip")
        assert url.startswith("http")


def test_redistricted_has_expected_six_states():
    expected = {"CA", "MO", "NC", "OH", "TX", "UT"}
    actual = {v[0] for v in REDISTRICTED.values()}
    assert actual == expected


def test_manual_reps_keys_are_tuples():
    for key in MANUAL_REPS:
        assert isinstance(key, tuple) and len(key) == 2
        state, dist = key
        assert isinstance(state, str) and isinstance(dist, str)


def test_manual_reps_values_have_name():
    for key, value in MANUAL_REPS.items():
        assert "name" in value, f"{key} override missing name"


# ── STATE_LEGISLATURE_META ───────────────────────────────────────────────────

LEG_REQUIRED_KEYS = {
    "body", "body_url_slug",
    "upper_chamber", "upper_member", "upper_url_slug",
    "lower_chamber", "lower_member", "lower_url_slug",
}


def test_legislature_meta_covers_all_50_states():
    assert set(STATE_LEGISLATURE_META.keys()) == ALL_50


def test_legislature_meta_has_all_required_keys():
    for abbr, meta in STATE_LEGISLATURE_META.items():
        missing = LEG_REQUIRED_KEYS - set(meta.keys())
        assert not missing, f"{abbr} missing keys: {missing}"


def test_legislature_meta_required_strings_non_empty():
    """Every state must have non-empty body, upper_chamber, upper_member, upper_url_slug."""
    for abbr, meta in STATE_LEGISLATURE_META.items():
        for key in ("body", "body_url_slug", "upper_chamber", "upper_member", "upper_url_slug"):
            assert meta[key], f"{abbr}.{key} is empty"


def test_legislature_meta_url_slugs_are_underscored():
    """No spaces in url slugs (Ballotpedia uses underscored names)."""
    for abbr, meta in STATE_LEGISLATURE_META.items():
        for key in ("body_url_slug", "upper_url_slug"):
            assert " " not in meta[key], f"{abbr}.{key} contains space"
        if meta["lower_url_slug"]:
            assert " " not in meta["lower_url_slug"]


def test_legislature_meta_nebraska_is_unicameral():
    ne = STATE_LEGISLATURE_META["NE"]
    assert ne["lower_chamber"] is None
    assert ne["lower_member"] is None
    assert ne["lower_url_slug"] is None
    # Body is "Nebraska Legislature"
    assert "Legislature" in ne["body"]


def test_legislature_meta_other_states_have_lower_chamber():
    """Every state except Nebraska must have a lower chamber."""
    for abbr, meta in STATE_LEGISLATURE_META.items():
        if abbr == "NE":
            continue
        assert meta["lower_chamber"], f"{abbr} unexpectedly has no lower_chamber"
        assert meta["lower_member"], f"{abbr} missing lower_member"
        assert meta["lower_url_slug"], f"{abbr} missing lower_url_slug"


def test_legislature_meta_member_titles_are_known():
    """Member titles should be one of the standard forms."""
    known = {"Senator", "Representative", "Delegate", "Assemblymember"}
    for abbr, meta in STATE_LEGISLATURE_META.items():
        assert meta["upper_member"] in known, f"{abbr} upper_member={meta['upper_member']!r}"
        if meta["lower_member"]:
            assert meta["lower_member"] in known, f"{abbr} lower_member={meta['lower_member']!r}"


def test_legislature_meta_specific_state_facts():
    """Spot-check a few states whose names matter most for correctness."""
    m = STATE_LEGISLATURE_META
    assert m["VA"]["body"] == "Virginia General Assembly"
    assert m["VA"]["upper_chamber"] == "Senate of Virginia"
    assert m["VA"]["lower_chamber"] == "Virginia House of Delegates"
    assert m["VA"]["lower_member"] == "Delegate"
    assert m["MA"]["body"] == "Massachusetts General Court"
    assert m["NH"]["body"] == "New Hampshire General Court"
    assert m["ND"]["body"] == "North Dakota Legislative Assembly"
    assert m["OR"]["body"] == "Oregon Legislative Assembly"
    assert m["CA"]["lower_chamber"] == "California State Assembly"
    assert m["CA"]["lower_member"] == "Assemblymember"
    assert m["NJ"]["lower_chamber"] == "New Jersey General Assembly"
    assert m["NJ"]["lower_member"] == "Assemblymember"
    assert m["MD"]["lower_member"] == "Delegate"
    assert m["WV"]["lower_member"] == "Delegate"
