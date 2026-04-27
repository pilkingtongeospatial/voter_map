"""
Voter Map Data Preparation Script (orchestrator)

Downloads and processes all data needed for the US Voter Information Map.

Produces:
  data/states.geojson                        State boundaries + 2024 election results
  data/congressional_districts_119.geojson   119th Congress district boundaries (current)
  data/congressional_districts.geojson       2026 expected districts (119th + 2025 redistricting)
  data/state_leg_upper.geojson               State legislative districts (upper chambers / senates)
  data/state_leg_lower.geojson               State legislative districts (lower chambers / houses)
  data/legislators.json                      Current US Congress legislators by state
  data/state_legislators.json                Current state legislators by state + chamber + district
  data/state_meta.json                       Voter registration links + election results

Note: 2025 redistricting ZIP files for CA, MO, NC, OH, TX, UT are auto-downloaded
from the American Redistricting Project (URLs in constants.py::REDISTRICTED) and
cached in data/redistricting_2025/. To override with a newer enacted map, drop a
replacement ZIP with the expected filename into that directory before running —
existing files are preferred over a fresh download.

The pipeline logic lives in constants.py, transforms.py, and io_helpers.py;
this file is just the orchestration and progress reporting.
"""

import json
import os
import sys

# Ensure this file works whether run as `python scripts/prep_data.py`
# or imported as `scripts.prep_data` from tests.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from constants import (  # noqa: E402
    ELECTION_2024,
    VOTER_REG,
    REDISTRICTED,
    STATE_LEGISLATURE_META,
    STATE_NAME_TO_ABBR,
    MANUAL_REPS,
)
from io_helpers import (  # noqa: E402
    download,
    pip_install,
    read_or_download,
    read_zip_shapefile,
    write_json,
)
from transforms import (  # noqa: E402
    annotate_states,
    apply_manual_overrides,
    build_state_meta,
    flatten_legislators,
    flatten_state_legislators,
    merge_cd_geojson,
    normalize_redistricted_feature,
    shapefile_bytes_to_geojson,
)


# ── lazy pyshp / pyyaml import (installs if missing) ─────────────────────────

def _ensure_deps():
    """Install pyshp and pyyaml if they aren't importable."""
    try:
        import shapefile  # noqa: F401
    except ImportError:
        print("Installing pyshp...")
        pip_install("pyshp")
    try:
        import yaml  # noqa: F401
    except ImportError:
        print("Installing pyyaml...")
        pip_install("pyyaml")


# ── pipeline stages ───────────────────────────────────────────────────────────

def stage_states(data_dir):
    print("\n[1/7] State boundaries")
    states_url = (
        "https://raw.githubusercontent.com/PublicaMundi/MappingAPI"
        "/master/data/geojson/us-states.json"
    )
    raw = download(states_url, "states GeoJSON")
    states_data = json.loads(raw)
    annotated = annotate_states(states_data, STATE_NAME_TO_ABBR, ELECTION_2024)

    path = os.path.join(data_dir, "states.geojson")
    write_json(path, annotated)
    print(f"  Saved {len(annotated['features'])} state features -> data/states.geojson")


def stage_cd119(data_dir, root_dir):
    print("\n[2/7] 119th Congress district boundaries (current representation)")
    local_zip = os.path.join(data_dir, "cb_2024_us_cd119_500k.zip")
    url = "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_cd119_500k.zip"
    shp_base = "cb_2024_us_cd119_500k"

    cached = os.path.exists(local_zip)
    zip_bytes = read_or_download(local_zip, url, "Census TIGER 119th Congress ZIP (~16 MB)")
    if cached:
        print(f"  Using cached zip: {os.path.relpath(local_zip, root_dir)}")
    else:
        print(f"  Cached to {os.path.relpath(local_zip, root_dir)}")

    print("  Converting shapefile -> GeoJSON...")
    shp, dbf, shx = read_zip_shapefile(zip_bytes, shp_base=shp_base)
    cd119_gj = shapefile_bytes_to_geojson(shp, dbf, shx)

    path = os.path.join(data_dir, "congressional_districts_119.geojson")
    write_json(path, cd119_gj)
    print(f"  Saved {len(cd119_gj['features'])} district features -> data/congressional_districts_119.geojson")
    return cd119_gj


def stage_cd_2026(cd119_gj, data_dir):
    print("\n[3/7] 2026 expected districts (119th + redistricting for CA, MO, NC, OH, TX, UT)")
    redist_dir = os.path.join(data_dir, "redistricting_2025")
    os.makedirs(redist_dir, exist_ok=True)

    # Download any missing redistricting ZIPs
    for fips in sorted(REDISTRICTED):
        abbr, zip_name, url = REDISTRICTED[fips]
        zip_path = os.path.join(redist_dir, zip_name)
        if os.path.exists(zip_path):
            print(f"  {abbr}: Using cached {zip_name}")
        else:
            data = download(url, f"{abbr} redistricting shapefile")
            with open(zip_path, "wb") as f:
                f.write(data)

    # Convert each redistricting shapefile, normalizing properties
    new_features = []
    for fips in sorted(REDISTRICTED):
        abbr, zip_name, _ = REDISTRICTED[fips]
        zip_path = os.path.join(redist_dir, zip_name)
        with open(zip_path, "rb") as f:
            zip_bytes = f.read()
        shp, dbf, shx = read_zip_shapefile(zip_bytes)  # auto-discover base
        gj = shapefile_bytes_to_geojson(shp, dbf, shx)
        for feat in gj["features"]:
            new_features.append(normalize_redistricted_feature(feat, fips))
        print(f"  {abbr}: {len(gj['features'])} redistricted districts")

    merged = merge_cd_geojson(cd119_gj, set(REDISTRICTED.keys()), new_features)
    kept_count = len(merged["features"]) - len(new_features)
    print(f"  Kept {kept_count} features from non-redistricted states")

    path = os.path.join(data_dir, "congressional_districts.geojson")
    write_json(path, merged)
    print(f"  Saved {len(merged['features'])} total features -> data/congressional_districts.geojson")
    print(f"  ({kept_count} unchanged + {len(new_features)} redistricted)")


def stage_legislators(data_dir):
    print("\n[4/7] Current US Congress legislators")
    import yaml  # imported here so dependency install happens before use
    leg_url = (
        "https://raw.githubusercontent.com/unitedstates/congress-legislators"
        "/main/legislators-current.yaml"
    )
    leg_raw = download(leg_url, "legislators-current.yaml")
    legislators_list = yaml.safe_load(leg_raw)
    upstream = flatten_legislators(legislators_list)
    by_state, applied = apply_manual_overrides(upstream, MANUAL_REPS)

    # Report which overrides actually filled a seat.
    for (state, dist), info in MANUAL_REPS.items():
        upstream_reps = (upstream.get(state) or {}).get("representatives", {})
        if dist not in upstream_reps:
            print(f"  Applied override: {state}-{dist} -> {info['name']}")

    if applied:
        print(f"  ({applied} override(s) applied)")
    else:
        print("  No overrides needed (all seats filled by upstream data)")

    path = os.path.join(data_dir, "legislators.json")
    write_json(path, by_state, indent=2)
    print(f"  Saved {len(by_state)} states -> data/legislators.json")


def stage_state_leg_districts(data_dir, root_dir):
    """Download Census SLDU + SLDL boundaries, write 2 GeoJSONs."""
    print("\n[5/7] State legislative district boundaries")

    # FIPS code from STATE_NAME_TO_ABBR is via the abbr-keyed map in states.geojson
    # but here we want abbr lookup keyed by STATEFP — done at consume time on the
    # frontend using FIPS_TO_ABBR. Pipeline just produces all-states GeoJSONs.

    layers = [
        ("upper", "cb_2024_us_sldu_500k", "state_leg_upper.geojson",
         "Census TIGER state legislative upper (~22 MB)"),
        ("lower", "cb_2024_us_sldl_500k", "state_leg_lower.geojson",
         "Census TIGER state legislative lower (~28 MB)"),
    ]
    for chamber, base, out_name, label in layers:
        local_zip = os.path.join(data_dir, f"{base}.zip")
        url = f"https://www2.census.gov/geo/tiger/GENZ2024/shp/{base}.zip"

        cached = os.path.exists(local_zip)
        zip_bytes = read_or_download(local_zip, url, label)
        if cached:
            print(f"  {chamber}: using cached {os.path.relpath(local_zip, root_dir)}")
        else:
            print(f"  {chamber}: cached to {os.path.relpath(local_zip, root_dir)}")

        shp, dbf, shx = read_zip_shapefile(zip_bytes, shp_base=base)
        gj = shapefile_bytes_to_geojson(shp, dbf, shx)
        path = os.path.join(data_dir, out_name)
        write_json(path, gj)
        print(f"  {chamber}: saved {len(gj['features'])} features -> data/{out_name}")


def stage_state_legislators(data_dir):
    """Download per-state OpenStates CSVs, flatten to one JSON keyed by state."""
    print("\n[6/7] Current state legislators (OpenStates)")
    import csv  # stdlib
    from io import StringIO

    rows = []
    abbrs = sorted(STATE_LEGISLATURE_META.keys())
    for abbr in abbrs:
        url = f"https://data.openstates.org/people/current/{abbr.lower()}.csv"
        try:
            raw = download(url, f"OpenStates {abbr}")
        except Exception as e:  # network / 404
            print(f"  {abbr}: skipped ({e})")
            continue
        text = raw.decode("utf-8", errors="replace")
        reader = csv.DictReader(StringIO(text))
        n_before = len(rows)
        for row in reader:
            row["state"] = abbr  # tag for the transform
            rows.append(row)
        print(f"  {abbr}: {len(rows) - n_before} legislators")

    by_state = flatten_state_legislators(rows)
    path = os.path.join(data_dir, "state_legislators.json")
    write_json(path, by_state, indent=2)

    total = sum(len(s.get("upper", {})) + len(s.get("lower", {})) for s in by_state.values())
    print(f"  Saved {total} legislators across {len(by_state)} states -> data/state_legislators.json")


def stage_state_meta(data_dir):
    print("\n[7/7] Voter registration links & election results")
    meta = build_state_meta(VOTER_REG, ELECTION_2024)
    path = os.path.join(data_dir, "state_meta.json")
    write_json(path, meta, indent=2)
    print(f"  Saved metadata for {len(meta)} states -> data/state_meta.json")


def _print_summary(data_dir):
    print("\nAll data preparation complete!")
    print(f"Data directory: {data_dir}")
    print()
    print("Files produced:")
    for name in [
        "states.geojson",
        "congressional_districts_119.geojson",
        "congressional_districts.geojson",
        "state_leg_upper.geojson",
        "state_leg_lower.geojson",
        "legislators.json",
        "state_legislators.json",
        "state_meta.json",
    ]:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / 1_048_576
            print(f"  {name:<45} {size_mb:6.1f} MB")


def main():
    _ensure_deps()
    root_dir = os.path.dirname(_SCRIPT_DIR)
    data_dir = os.path.join(root_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    stage_states(data_dir)
    cd119_gj = stage_cd119(data_dir, root_dir)
    stage_cd_2026(cd119_gj, data_dir)
    stage_legislators(data_dir)
    stage_state_leg_districts(data_dir, root_dir)
    stage_state_legislators(data_dir)
    stage_state_meta(data_dir)
    _print_summary(data_dir)


if __name__ == "__main__":
    main()
