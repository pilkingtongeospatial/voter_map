"""
PostGIS database helpers for the voter map pipeline.

DATABASE_URL env var (default: postgresql://localhost/voter_map) controls the
connection.  Swap to any PostgreSQL+PostGIS instance by changing that variable.

Dependencies (auto-installed by prep_data.py if absent):
    sqlalchemy, psycopg2-binary, shapely
"""

import os
import re

SCHEMA = "voter_map_states"
DEFAULT_DB_URL = "postgresql://localhost/voter_map"
SRID = 4326


# ── connection ─────────────────────────────────────────────────────────────────

def get_engine():
    from sqlalchemy import create_engine
    url = os.environ.get("DATABASE_URL", DEFAULT_DB_URL)
    return create_engine(url)


# ── geometry helpers ───────────────────────────────────────────────────────────

def _shapely(geom_dict):
    """GeoJSON geometry dict → Shapely geometry (repaired if invalid), or None."""
    import shapely.geometry as sg
    if not geom_dict:
        return None
    s = sg.shape(geom_dict)
    return s if s.is_valid else s.buffer(0)


def _wkt(geom_dict):
    """Return WKT string for the geometry, or None."""
    s = _shapely(geom_dict)
    return s.wkt if s else None


def _bbox(geom_dict):
    """Return [minx, miny, maxx, maxy] or None."""
    s = _shapely(geom_dict)
    return list(s.bounds) if s else None


def _strip_leading_zeros(raw):
    """'005' → '5',  '012B' → '12B',  '5' → '5'."""
    return re.sub(r"^0+(?=\d)", "", str(raw)).strip()


# ── DDL ────────────────────────────────────────────────────────────────────────

_SCHEMA_DDL = f"""
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS {SCHEMA}
"""

_DROP_DDL = f"""
DROP TABLE IF EXISTS {SCHEMA}.state_legislators CASCADE;
DROP TABLE IF EXISTS {SCHEMA}.state_meta CASCADE;
DROP TABLE IF EXISTS {SCHEMA}.state_leg_lower CASCADE;
DROP TABLE IF EXISTS {SCHEMA}.state_leg_upper CASCADE;
DROP TABLE IF EXISTS {SCHEMA}.congressional_districts CASCADE;
DROP TABLE IF EXISTS {SCHEMA}.congressional_districts_119 CASCADE;
DROP TABLE IF EXISTS {SCHEMA}.legislators CASCADE;
DROP TABLE IF EXISTS {SCHEMA}.us_states CASCADE
"""

_TABLE_DDL = f"""
CREATE TABLE {SCHEMA}.us_states (
    state_fp          VARCHAR(2)    PRIMARY KEY,
    state_name        VARCHAR(100)  NOT NULL,
    abbr              VARCHAR(2)    NOT NULL UNIQUE,
    party             VARCHAR(1),
    density           FLOAT,
    registration_link TEXT,
    registration_name TEXT,
    geometry          geometry(Geometry, {SRID}) NOT NULL
);

CREATE TABLE {SCHEMA}.legislators (
    id               SERIAL        PRIMARY KEY,
    state_fp         VARCHAR(2)    NOT NULL REFERENCES {SCHEMA}.us_states(state_fp),
    state_name       VARCHAR(100),
    body             VARCHAR(8)    NOT NULL,
    district         VARCHAR(32),
    name             VARCHAR(200)  NOT NULL,
    party            VARCHAR(64),
    url              TEXT,
    vacant           BOOLEAN       NOT NULL DEFAULT FALSE,
    vacancy_reason   TEXT
);

CREATE TABLE {SCHEMA}.congressional_districts_119 (
    id               SERIAL        PRIMARY KEY,
    state_fp         VARCHAR(2)    NOT NULL REFERENCES {SCHEMA}.us_states(state_fp),
    cd119fp          VARCHAR(2)    NOT NULL,
    namelsad         VARCHAR(200),
    geoid            VARCHAR(4),
    bbox             FLOAT[],
    geometry         geometry(Geometry, {SRID}) NOT NULL
);

CREATE TABLE {SCHEMA}.congressional_districts (
    id               SERIAL        PRIMARY KEY,
    state_fp         VARCHAR(2)    NOT NULL REFERENCES {SCHEMA}.us_states(state_fp),
    cd119fp          VARCHAR(2)    NOT NULL,
    namelsad         VARCHAR(200),
    geoid            VARCHAR(4),
    bbox             FLOAT[],
    geometry         geometry(Geometry, {SRID}) NOT NULL
);

CREATE TABLE {SCHEMA}.state_leg_upper (
    id               SERIAL        PRIMARY KEY,
    state_fp         VARCHAR(2)    NOT NULL REFERENCES {SCHEMA}.us_states(state_fp),
    state_name       VARCHAR(100),
    namelsad         VARCHAR(200),
    name             VARCHAR(200),
    sldust           VARCHAR(32),
    geometry         geometry(Geometry, {SRID}) NOT NULL
);

CREATE TABLE {SCHEMA}.state_leg_lower (
    id               SERIAL        PRIMARY KEY,
    state_fp         VARCHAR(2)    NOT NULL REFERENCES {SCHEMA}.us_states(state_fp),
    state_name       VARCHAR(100),
    namelsad         VARCHAR(200),
    name             VARCHAR(200),
    sldlst           VARCHAR(32),
    geometry         geometry(Geometry, {SRID}) NOT NULL
);

CREATE TABLE {SCHEMA}.state_meta (
    state_fp         VARCHAR(2)    PRIMARY KEY REFERENCES {SCHEMA}.us_states(state_fp),
    voter_reg_url    TEXT,
    voter_reg_name   TEXT,
    party            VARCHAR(1)
);

CREATE TABLE {SCHEMA}.state_legislators (
    id               SERIAL        PRIMARY KEY,
    state_fp         VARCHAR(2)    NOT NULL REFERENCES {SCHEMA}.us_states(state_fp),
    state_name       VARCHAR(100),
    chamber          VARCHAR(8)    NOT NULL,
    district         VARCHAR(64)   NOT NULL,
    name             VARCHAR(200)  NOT NULL,
    party            VARCHAR(64)
)
"""

_INDEX_DDL = f"""
CREATE INDEX ON {SCHEMA}.us_states USING GIST (geometry);
CREATE INDEX ON {SCHEMA}.us_states (abbr);

CREATE INDEX ON {SCHEMA}.legislators (state_fp);
CREATE INDEX ON {SCHEMA}.legislators (state_fp, body);
CREATE INDEX ON {SCHEMA}.legislators (state_fp, body, district);

CREATE INDEX ON {SCHEMA}.congressional_districts_119 USING GIST (geometry);
CREATE INDEX ON {SCHEMA}.congressional_districts_119 (state_fp);
CREATE INDEX ON {SCHEMA}.congressional_districts_119 (geoid);

CREATE INDEX ON {SCHEMA}.congressional_districts USING GIST (geometry);
CREATE INDEX ON {SCHEMA}.congressional_districts (state_fp);
CREATE INDEX ON {SCHEMA}.congressional_districts (geoid);

CREATE INDEX ON {SCHEMA}.state_leg_upper USING GIST (geometry);
CREATE INDEX ON {SCHEMA}.state_leg_upper (state_fp);
CREATE INDEX ON {SCHEMA}.state_leg_upper (state_fp, name);

CREATE INDEX ON {SCHEMA}.state_leg_lower USING GIST (geometry);
CREATE INDEX ON {SCHEMA}.state_leg_lower (state_fp);
CREATE INDEX ON {SCHEMA}.state_leg_lower (state_fp, name);

CREATE INDEX ON {SCHEMA}.state_meta (state_fp);

CREATE INDEX ON {SCHEMA}.state_legislators (state_fp);
CREATE INDEX ON {SCHEMA}.state_legislators (state_fp, chamber);
CREATE INDEX ON {SCHEMA}.state_legislators (state_fp, chamber, district)
"""


def _exec_ddl(conn, sql):
    from sqlalchemy import text
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(text(stmt))


def create_schema_and_tables(engine):
    """Create schema + all tables, dropping any prior version first."""
    with engine.begin() as conn:
        _exec_ddl(conn, _SCHEMA_DDL)
        _exec_ddl(conn, _DROP_DDL)
        _exec_ddl(conn, _TABLE_DDL)


def create_indices(engine):
    """Add spatial and attribute indices after data is loaded."""
    with engine.begin() as conn:
        _exec_ddl(conn, _INDEX_DDL)


# ── generic insert helper ──────────────────────────────────────────────────────

def _insert_batch_pg(conn, table_path, columns, rows, geom_col=None):
    """
    Insert rows via psycopg2.extras.execute_values.

    Used when columns include FLOAT[] (bbox) because psycopg2 adapts Python
    lists to PostgreSQL arrays natively, bypassing SQLAlchemy's type compiler.
    """
    from psycopg2.extras import execute_values

    tpl_parts = []
    for c in columns:
        if c == geom_col:
            tpl_parts.append(f"ST_SetSRID(ST_GeomFromText(%s), {SRID})")
        else:
            tpl_parts.append("%s")

    sql = f"INSERT INTO {table_path} ({', '.join(columns)}) VALUES %s"
    template = f"({', '.join(tpl_parts)})"
    data = [tuple(row[c] for c in columns) for row in rows]

    cur = conn.connection.cursor()
    BATCH = 500
    try:
        for i in range(0, len(data), BATCH):
            execute_values(cur, sql, data[i : i + BATCH], template=template)
    finally:
        cur.close()


def _insert_batch(conn, table_path, columns, rows, geom_col=None, bbox_cols=None):
    """
    Execute a parameterized INSERT for a list of row dicts.

    geom_col  : column whose value is a WKT string; wrapped with
                ST_SetSRID(ST_GeomFromText(...), SRID) in the SQL.
    bbox_cols : columns whose values are Python lists [minx,miny,maxx,maxy];
                when present, delegates to _insert_batch_pg so psycopg2 can
                adapt the lists to FLOAT[] natively.
    """
    from sqlalchemy import text

    if not rows:
        return

    if bbox_cols:
        _insert_batch_pg(conn, table_path, columns, rows, geom_col=geom_col)
        return

    special = {geom_col} if geom_col else set()
    plain = [c for c in columns if c not in special]

    col_parts = list(plain)
    ph_parts = [f":{c}" for c in plain]

    if geom_col:
        col_parts.append(geom_col)
        ph_parts.append(f"ST_SetSRID(ST_GeomFromText(:{geom_col}), {SRID})")

    sql = text(
        f"INSERT INTO {table_path} ({', '.join(col_parts)}) "
        f"VALUES ({', '.join(ph_parts)})"
    )

    BATCH = 500
    for i in range(0, len(rows), BATCH):
        conn.execute(sql, rows[i : i + BATCH])


# ── per-table insert functions ─────────────────────────────────────────────────

def insert_us_states(engine, states_gj, voter_reg, abbr_to_fips):
    """Populate voter_map_states.us_states from states GeoJSON + VOTER_REG."""
    rows = []
    for feat in states_gj.get("features", []):
        props = feat.get("properties") or {}
        abbr = props.get("abbr", "")
        state_fp = abbr_to_fips.get(abbr)
        if not state_fp:
            continue  # territories without a FIPS entry (e.g. PR, GU) excluded
        reg = voter_reg.get(abbr, {})
        rows.append({
            "state_fp": state_fp,
            "state_name": props.get("name", ""),
            "abbr": abbr,
            "party": props.get("party", ""),
            "density": props.get("density"),
            "registration_link": reg.get("url", ""),
            "registration_name": reg.get("name", ""),
            "geometry": _wkt(feat.get("geometry")),
        })

    cols = [
        "state_fp", "state_name", "abbr", "party", "density",
        "registration_link", "registration_name", "geometry",
    ]
    with engine.begin() as conn:
        _insert_batch(conn, f"{SCHEMA}.us_states", cols, rows, geom_col="geometry")
    return len(rows)


def insert_legislators(engine, legislators_by_state, abbr_to_fips, abbr_to_state_name):
    """Populate voter_map_states.legislators from the flattened legislators dict."""
    rows = []
    for abbr, data in legislators_by_state.items():
        state_fp = abbr_to_fips.get(abbr)
        if not state_fp:
            continue
        state_name = abbr_to_state_name.get(abbr, abbr)

        for sen in data.get("senators", []):
            rows.append({
                "state_fp": state_fp,
                "state_name": state_name,
                "body": "senate",
                "district": None,
                "name": sen.get("name", ""),
                "party": sen.get("party", ""),
                "url": sen.get("url", "") or "",
                "vacant": bool(sen.get("vacant", False)),
                "vacancy_reason": sen.get("vacancy_reason"),
            })

        for dist, rep in data.get("representatives", {}).items():
            rows.append({
                "state_fp": state_fp,
                "state_name": state_name,
                "body": "house",
                "district": str(dist),
                "name": rep.get("name", ""),
                "party": rep.get("party", ""),
                "url": rep.get("url", "") or "",
                "vacant": bool(rep.get("vacant", False)),
                "vacancy_reason": rep.get("vacancy_reason"),
            })

    cols = [
        "state_fp", "state_name", "body", "district", "name",
        "party", "url", "vacant", "vacancy_reason",
    ]
    with engine.begin() as conn:
        _insert_batch(conn, f"{SCHEMA}.legislators", cols, rows)
    return len(rows)


def _cd_rows_from_gj(gj, valid_fips=None):
    rows = []
    for feat in gj.get("features", []):
        props = feat.get("properties") or {}
        state_fp = (props.get("STATEFP") or props.get("statefp") or "").strip()
        if not state_fp:
            continue
        if valid_fips and state_fp not in valid_fips:
            continue
        geom = feat.get("geometry")
        rows.append({
            "state_fp": state_fp,
            "cd119fp": (props.get("CD119FP") or props.get("cd119fp") or "").strip(),
            "namelsad": props.get("NAMELSAD") or props.get("namelsad") or "",
            "geoid": props.get("GEOID") or props.get("geoid") or "",
            "bbox": _bbox(geom),
            "geometry": _wkt(geom),
        })
    return rows


def insert_congressional_districts_119(engine, gj, valid_fips=None):
    rows = _cd_rows_from_gj(gj, valid_fips=valid_fips)
    cols = ["state_fp", "cd119fp", "namelsad", "geoid", "bbox", "geometry"]
    with engine.begin() as conn:
        _insert_batch(
            conn, f"{SCHEMA}.congressional_districts_119", cols, rows,
            geom_col="geometry", bbox_cols=["bbox"],
        )
    return len(rows)


def insert_congressional_districts(engine, gj, valid_fips=None):
    rows = _cd_rows_from_gj(gj, valid_fips=valid_fips)
    cols = ["state_fp", "cd119fp", "namelsad", "geoid", "bbox", "geometry"]
    with engine.begin() as conn:
        _insert_batch(
            conn, f"{SCHEMA}.congressional_districts", cols, rows,
            geom_col="geometry", bbox_cols=["bbox"],
        )
    return len(rows)


def insert_state_leg_upper(engine, gj, fips_to_abbr, abbr_to_state_name):
    rows = []
    for feat in gj.get("features", []):
        props = feat.get("properties") or {}
        state_fp = (props.get("STATEFP") or "").strip()
        if not state_fp:
            continue
        abbr = fips_to_abbr.get(state_fp, "")
        if not abbr:
            continue
        sldust = (props.get("SLDUST") or "").strip()
        name = (props.get("NAME") or "").strip()
        if not name and sldust:
            name = _strip_leading_zeros(sldust)
        rows.append({
            "state_fp": state_fp,
            "state_name": abbr_to_state_name.get(abbr, ""),
            "namelsad": props.get("NAMELSAD") or "",
            "name": name,
            "sldust": sldust,
            "geometry": _wkt(feat.get("geometry")),
        })
    cols = ["state_fp", "state_name", "namelsad", "name", "sldust", "geometry"]
    with engine.begin() as conn:
        _insert_batch(
            conn, f"{SCHEMA}.state_leg_upper", cols, rows, geom_col="geometry"
        )
    return len(rows)


def insert_state_leg_lower(engine, gj, fips_to_abbr, abbr_to_state_name):
    rows = []
    for feat in gj.get("features", []):
        props = feat.get("properties") or {}
        state_fp = (props.get("STATEFP") or "").strip()
        if not state_fp:
            continue
        abbr = fips_to_abbr.get(state_fp, "")
        if not abbr:
            continue
        sldlst = (props.get("SLDLST") or "").strip()
        name = (props.get("NAME") or "").strip()
        if not name and sldlst:
            name = _strip_leading_zeros(sldlst)
        rows.append({
            "state_fp": state_fp,
            "state_name": abbr_to_state_name.get(abbr, ""),
            "namelsad": props.get("NAMELSAD") or "",
            "name": name,
            "sldlst": sldlst,
            "geometry": _wkt(feat.get("geometry")),
        })
    cols = ["state_fp", "state_name", "namelsad", "name", "sldlst", "geometry"]
    with engine.begin() as conn:
        _insert_batch(
            conn, f"{SCHEMA}.state_leg_lower", cols, rows, geom_col="geometry"
        )
    return len(rows)


def insert_state_meta(engine, meta_by_abbr, abbr_to_fips):
    rows = []
    for abbr, data in meta_by_abbr.items():
        state_fp = abbr_to_fips.get(abbr)
        if not state_fp:
            continue
        reg = data.get("voter_reg") or {}
        rows.append({
            "state_fp": state_fp,
            "voter_reg_url": reg.get("url", ""),
            "voter_reg_name": reg.get("name", ""),
            "party": data.get("party", ""),
        })
    cols = ["state_fp", "voter_reg_url", "voter_reg_name", "party"]
    with engine.begin() as conn:
        _insert_batch(conn, f"{SCHEMA}.state_meta", cols, rows)
    return len(rows)


def insert_state_legislators(engine, legislators_by_state, abbr_to_fips, abbr_to_state_name):
    rows = []
    for abbr, chambers in legislators_by_state.items():
        state_fp = abbr_to_fips.get(abbr)
        if not state_fp:
            continue
        state_name = abbr_to_state_name.get(abbr, abbr)
        for chamber in ("upper", "lower"):
            for district, member in (chambers.get(chamber) or {}).items():
                rows.append({
                    "state_fp": state_fp,
                    "state_name": state_name,
                    "chamber": chamber,
                    "district": str(district),
                    "name": member.get("name", ""),
                    "party": member.get("party", ""),
                })
    cols = ["state_fp", "state_name", "chamber", "district", "name", "party"]
    with engine.begin() as conn:
        _insert_batch(conn, f"{SCHEMA}.state_legislators", cols, rows)
    return len(rows)
