"""Data integrity tests for scripts/constants.py."""

from constants import (
    ABBR_TO_STATE_NAME,
    ELECTION_2024,
    MANUAL_REPS,
    REDISTRICTED,
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
