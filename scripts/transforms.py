"""
Pure data transformation functions for the voter map pipeline.

Every function here is deterministic and side-effect-free: no network I/O,
no file reads/writes, no subprocess calls. All inputs are plain Python
objects; outputs are new plain Python objects. None of these functions
mutates its inputs.

These are the functions that are unit-tested in tests/python/test_transforms.py.
"""

from copy import deepcopy


def annotate_states(raw_geojson, name_to_abbr, election_results):
    """Return a new GeoJSON dict with 'abbr' and 'party' added to each feature.

    Looks up each feature's ``properties.name`` in ``name_to_abbr`` to assign
    ``abbr``, then looks up that abbr in ``election_results`` to assign
    ``party``. Unknown names yield empty strings (no KeyError).

    The input dict is not mutated.
    """
    out = deepcopy(raw_geojson)
    for feat in out.get("features", []):
        props = feat.setdefault("properties", {})
        name = props.get("name", "")
        abbr = name_to_abbr.get(name, "")
        props["abbr"] = abbr
        props["party"] = election_results.get(abbr, "")
    return out


def shapefile_bytes_to_geojson(shp, dbf, shx):
    """Convert raw shapefile byte-strings to a GeoJSON FeatureCollection dict.

    Uses pyshp. Imported lazily so this module can be imported in test
    environments that don't have pyshp installed (the tests that don't
    exercise this function will still work).
    """
    import io as _io
    import shapefile as _shapefile
    reader = _shapefile.Reader(
        shp=_io.BytesIO(shp),
        dbf=_io.BytesIO(dbf),
        shx=_io.BytesIO(shx),
    )
    return reader.__geo_interface__


def normalize_redistricted_feature(feat, fips):
    """Return a new feature with properties normalized to the Census schema.

    Given a raw GeoJSON feature from a 2025 redistricting shapefile (whose
    properties use ad-hoc names like DISTRICT, DIST_NAME, ST), return a new
    feature where ``properties`` contains exactly the keys:

        STATEFP, CD119FP, NAMELSAD, GEOID, CDSESSN, SOURCE

    Missing fields fall back to sensible defaults. CD119FP is zero-padded
    to 2 digits. Input is not mutated.
    """
    props = feat.get("properties", {}) or {}
    dist_num = str(int(props.get("DISTRICT", "0")))
    cd = dist_num.zfill(2)
    statefp = props.get("ST", fips)
    new_feat = deepcopy(feat)
    new_feat["properties"] = {
        "STATEFP": statefp,
        "CD119FP": cd,
        "NAMELSAD": props.get("DIST_NAME", f"Congressional District {dist_num}"),
        "GEOID": statefp + cd,
        "CDSESSN": "119",
        "SOURCE": "redistricting_2025",
    }
    return new_feat


def merge_cd_geojson(base_geojson, redistricted_fips, new_features):
    """Return a new FeatureCollection: base minus redistricted-state features, plus new_features.

    ``redistricted_fips`` is an iterable of FIPS codes (strings). Any feature
    in ``base_geojson`` whose ``STATEFP`` is in this set is dropped; the
    ``new_features`` list is appended after the survivors.
    """
    redistricted_set = set(redistricted_fips)
    kept = [
        deepcopy(f) for f in base_geojson.get("features", [])
        if (f.get("properties") or {}).get("STATEFP", "") not in redistricted_set
    ]
    return {
        "type": "FeatureCollection",
        "features": kept + [deepcopy(f) for f in new_features],
    }


def flatten_legislators(legislators_list):
    """Transform the raw congress-legislators YAML list into by-state dict form.

    Output structure::

        {
          "CA": {
            "senators": [{"name": ..., "party": ..., "url": ...}, ...],
            "representatives": {"1": {...}, "2": {...}, ...}
          },
          ...
        }

    Rules:
      - Legislators with no ``terms`` are skipped.
      - The last entry in ``terms`` is used (current term).
      - ``name.official_full`` is preferred; falls back to ``first + last``.
      - Missing ``district`` is stored under key ``"0"``.
      - Missing ``url``/``party`` become ``""`` / ``"Unknown"``.
    """
    by_state = {}
    for leg in legislators_list or []:
        terms = leg.get("terms") or []
        if not terms:
            continue
        term = terms[-1]
        state = term.get("state", "")
        typ = term.get("type", "")
        party = term.get("party", "Unknown")
        url = term.get("url", "") or ""
        name_d = leg.get("name") or {}
        full = name_d.get("official_full", "") or (
            f"{name_d.get('first', '')} {name_d.get('last', '')}".strip()
        )

        if state not in by_state:
            by_state[state] = {"senators": [], "representatives": {}}

        info = {"name": full, "party": party, "url": url}

        if typ == "sen":
            by_state[state]["senators"].append(info)
        elif typ == "rep":
            district = term.get("district", 0) or 0
            by_state[state]["representatives"][str(district)] = info

    return by_state


def apply_manual_overrides(by_state, overrides):
    """Return (updated_by_state, n_applied).

    For each ``(state, dist) -> info`` entry in ``overrides``, fill
    ``by_state[state]["representatives"][dist]`` only if upstream data
    did not already fill that seat. Returns a new dict; input is not mutated.
    """
    out = deepcopy(by_state)
    applied = 0
    for (state, dist), info in overrides.items():
        if state not in out:
            out[state] = {"senators": [], "representatives": {}}
        reps = out[state].setdefault("representatives", {})
        if dist not in reps:
            reps[dist] = dict(info)  # copy to prevent shared refs
            applied += 1
    return out, applied


def build_state_meta(voter_reg, election_results):
    """Combine voter registration + election results into the state_meta structure.

    Output::

        { "CA": { "voter_reg": {"url": ..., "name": ...}, "party": "D" }, ... }

    Only abbrs present in ``voter_reg`` appear in the output.
    Unknown abbrs in ``election_results`` become ``party=""``.
    """
    meta = {}
    for abbr, reg in voter_reg.items():
        meta[abbr] = {
            "voter_reg": dict(reg),  # shallow copy
            "party": election_results.get(abbr, ""),
        }
    return meta
