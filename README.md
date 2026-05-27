# US Voter Information Map

An interactive map of the United States showing 2024 Presidential Election results by state, with federal congressional and state legislative district boundaries and links to voter registration, current representatives, state legislators, and 2026 midterm candidate information.

## Prerequisites

- Python 3.7+
- Internet connection (for initial data download)

## Quick Start

### 1. Download the data

Run the data preparation script once to download all map data:

```bash
python scripts/prep_data.py
```

This downloads and processes (~140 MB total):
- State boundary GeoJSON (PublicaMundi / US Census TIGER)
- 119th Congress district boundaries (US Census TIGER, ~16 MB)
- 2026 expected district boundaries: 119th + 2025 redistricting shapefiles auto-downloaded from the [American Redistricting Project](https://thearp.org) for CA, MO, NC, OH, TX, UT (~60 MB)
- State legislative upper-chamber boundaries (US Census TIGER, ~22 MB)
- State legislative lower-chamber boundaries (US Census TIGER, ~28 MB)
- Current US Congress legislators (unitedstates/congress-legislators), with manual overrides for known vacancies
- Current state legislators for all 50 states ([OpenStates / Plural Policy](https://open.pluralpolicy.com), ~7,000 legislators)
- Voter registration links for all 50 states

Required packages (`pyshp`, `pyyaml`) are installed automatically if missing.

#### 2025 redistricting data

Six states had redistricting take effect for 2026: CA, MO, NC, OH, TX, UT. Their shapefiles are downloaded automatically from the URLs listed in `scripts/constants.py::REDISTRICTED` into `data/redistricting_2025/` and cached on disk for reuse.

To override the upstream source (e.g. to use a newer enacted map or a court-ordered revision before the URL is updated), drop a replacement ZIP into `data/redistricting_2025/` with the expected filename before running the script — an existing file is always preferred over a fresh download:

| File | State |
|---|---|
| `CA_CD_2025.zip` | California |
| `MO_CD_2025.zip` | Missouri |
| `NC_CD_2025.zip` | North Carolina |
| `OH_CD_2025.zip` | Ohio |
| `TX_CD_2025.zip` | Texas |
| `UT_CD_2025.zip` | Utah |

### 2. Start the local server

```bash
python serve.py
```

This starts a local server at `http://localhost:8000` and opens the map in your default browser automatically.

## Using the Map

- **Click any state** to zoom in and see district boundaries, U.S. Senators, and a voter registration link
- **Toggle between views** using the two grouped pickers in the sidebar:
  - **Federal Districts** — Current (119th Congress) or 2026 Expected
  - **State Legislature** — upper or lower chamber, labeled by each state's actual chamber name (e.g. *Senate of Virginia*, *California State Assembly*, *Virginia House of Delegates*)
- **Click a congressional district** to see the current representative and a link to 2026 Ballotpedia candidate information
- **Click a state legislative district** to see the current state legislator (titled correctly as *Senator*, *Delegate*, *Assemblymember*, etc.) and a Ballotpedia link to that district
- **Vacant seats** are labeled with the reason and upcoming special election date
- **Use the back buttons** in the sidebar to navigate back to a state or national view
- **Alaska and Hawaii** appear in inset maps in the bottom-left corner

### District views

| View | Boundaries shown |
|---|---|
| Federal: Current Districts | 119th Congress (in effect now) |
| Federal: 2026 Expected | 119th Congress + 2025 redistricting for CA, MO, NC, OH, TX, UT |
| State: upper chamber | State senate districts (Census 2024 cartographic boundaries) |
| State: lower chamber | State house / assembly / house of delegates districts |

### State legislature naming

The sidebar uses each state's actual terminology for its legislative body, chambers, and members. A click on a Virginia state senate district shows the legislator titled "Senator", under the heading "Senate of Virginia", with a reference to the parent body "Virginia General Assembly". A click on a Virginia state house district shows "Delegate" in the "Virginia House of Delegates". California uses "Assemblymember" / "California State Assembly". Massachusetts uses "Massachusetts General Court" as the body name. Nebraska is unicameral — only the upper-chamber toggle appears, and the body is "Nebraska Legislature". DC and territories have no state legislature toggle.

The full mapping lives in `scripts/constants.py::STATE_LEGISLATURE_META` (mirrored to `js/constants.js`) and is data-integrity-tested for all 50 states.

## Updating Data

Re-run the prep script at any time to refresh legislator and district data:

```bash
python scripts/prep_data.py
```

The 119th Congress ZIP is cached locally after the first run and reused automatically.

The script includes manual overrides for seats not yet reflected in the upstream `congress-legislators` data (e.g., recent special election winners and current vacancies). These are applied only when the upstream data is missing — once the source catches up, the override is skipped.

## File Structure

```
voter_map/
├── index.html              # HTML shell (imports js/main.js as ES module)
├── serve.py                # Local HTTP server
├── README.md
├── CNAME                   # GitHub Pages custom domain
├── .gitignore
├── .gitattributes          # LF line endings for shell scripts
├── pyproject.toml          # pytest config
├── package.json            # vitest dev dependency
├── vitest.config.js        # Vitest config
├── js/                     # Browser ES modules
│   ├── constants.js        # Party colors, FIPS lookups, centroids
│   ├── utils.js            # Pure helpers (partyClass, stateStyle, ...)
│   ├── panels.js           # Pure sidebar-HTML generators
│   ├── map.js              # Leaflet layer builders
│   └── main.js             # Entry point & event wiring
├── scripts/
│   ├── prep_data.py        # Pipeline orchestrator
│   ├── constants.py        # Election/voter-reg/redistricting constants
│   ├── transforms.py       # Pure data-transformation functions
│   └── io_helpers.py       # Network/filesystem wrappers
├── tests/
│   ├── python/             # pytest unit tests
│   │   ├── conftest.py
│   │   ├── test_constants.py
│   │   ├── test_transforms.py
│   │   └── test_io_helpers.py
│   └── js/                 # vitest unit tests
│       ├── constants.test.js
│       ├── utils.test.js
│       └── panels.test.js
├── hooks/
│   ├── pre-commit          # Runs pytest + vitest on every commit
│   └── install-hooks.sh    # One-time installer
└── data/                   # Generated by prep_data.py (gitignored)
    ├── states.geojson
    ├── congressional_districts_119.geojson
    ├── congressional_districts.geojson
    ├── state_leg_upper.geojson
    ├── state_leg_lower.geojson
    ├── legislators.json
    ├── state_legislators.json
    ├── state_meta.json
    ├── cb_2024_us_cd119_500k.zip
    ├── cb_2024_us_sldu_500k.zip
    ├── cb_2024_us_sldl_500k.zip
    └── redistricting_2025/
```

## Development

### Running tests

```bash
# Python tests
python -m pytest tests/python/

# JavaScript tests (requires Node.js)
npm install     # one-time
npm test
```

### Pre-commit hook

A git hook runs both test suites before every commit. Install it once per clone:

```bash
bash hooks/install-hooks.sh
```

The hook lives in `hooks/pre-commit` and is version-controlled. If Node.js
is not installed, the JS tests are skipped with a warning and only the
Python suite gates the commit.

### Module architecture

The pipeline and client are split into pure functions (easily testable) and
thin I/O / DOM wrappers (mockable). See `scripts/transforms.py` and
`js/utils.js` / `js/panels.js` for the pure code; tests in `tests/` cover
every exported function.

## Changelog

### [1.4.0] - 2026-04-26
#### Added
- State legislative districts for all 50 states + DC, both upper and lower chambers, sourced from US Census Cartographic Boundary files (`cb_2024_us_sldu_500k`, `cb_2024_us_sldl_500k`)
- Current state legislator data (~6,800 members across 50 states) sourced from the [OpenStates / Plural Policy](https://open.pluralpolicy.com) public-domain bulk CSVs
- Two-group view toggle in the per-state sidebar: **Federal Districts** (Current / 2026 Expected) and **State Legislature** (upper / lower chamber, labeled by each state's actual chamber name)
- Per-state legislative naming table (`STATE_LEGISLATURE_META`) covering the body name, chamber names, member titles ("Senator" / "Delegate" / "Assemblymember" / "Representative"), and Ballotpedia URL slugs for every state
- New state-leg district panel: title-prefixed legislator name (e.g. "Senator Aaron Rouse", "Delegate Lee Ware", "Assemblymember Gail Pellerin"), state-correct chamber heading (e.g. "Senate of Virginia"), parent-body link, and a Ballotpedia district link
- Special-case handling for unicameral Nebraska (lower-chamber toggle suppressed), Massachusetts/New Hampshire ("General Court" body), Virginia/Maryland/West Virginia ("Delegates"), California/NY/NV/NJ ("Assembly" lower chambers), and DC/territories (entire state-leg group hidden)
- 16 new pytest cases (transforms + naming-table integrity) and 50 new vitest cases (chamber helpers, state-leg panel rendering, naming-table integrity)

#### Changed
- `prep_data.py` pipeline grew from 5 stages to 7 (adds `stage_state_leg_districts` and `stage_state_legislators`)
- `flatten_state_legislators` transform handles OpenStates' Nebraska-specific `current_chamber: "legislature"` value by remapping it to `"upper"`, and joins names for multi-member districts with " / "
- Welcome panel and sidebar copy updated to reference state legislative districts, not just federal congressional districts
- Generated data total grew from ~80 MB to ~140 MB (the two new SLD GeoJSONs are ~22 MB and ~28 MB; the new state_legislators.json is ~0.6 MB)

### [1.3.0] - 2026-04-19
#### Changed
- Inline JavaScript in `index.html` extracted into ES modules under `js/` (`constants.js`, `utils.js`, `panels.js`, `map.js`, `main.js`); `index.html` is now a thin shell that imports `js/main.js` as a module
- `scripts/prep_data.py` split into a thin orchestrator over pure modules (`constants.py`, `transforms.py`, `io_helpers.py`) guarded by `if __name__ == "__main__"` so imports don't trigger downloads
- Sidebar panels switched from inline `onclick` handlers to `data-action` attributes with event delegation, so panel generators stay pure (no globals, no `document` access)

#### Added
- Python unit-test suite (pytest) under `tests/python/` — 51 tests covering constants, pure transforms, and I/O helpers with mocked network/filesystem
- JavaScript unit-test suite (Vitest) under `tests/js/` — covers constants, utils, and panel HTML generators in a Node environment
- Version-controlled pre-commit hook (`hooks/pre-commit` + `hooks/install-hooks.sh`) that runs both suites before every commit; soft-skips the JS suite with a warning when Node.js is unavailable so the Python suite still gates the commit
- `pyproject.toml` (pytest config), `package.json` + `vitest.config.js` (Vitest config), and `.gitattributes` to keep LF line endings on the shell scripts across platforms
- Development section in this README covering test commands and hook installation

#### Fixed
- `districtNumFromProps` now uses `"key" in props` existence checks instead of `||` chaining, so at-large districts with `CD119FP: "00"` are no longer mis-read as falsy
- `ABBR_TO_FIPS` lookup is precomputed once instead of scanning `FIPS_TO_ABBR` with `.find()` on every call

### [1.2.0] - 2026-04-11
#### Changed
- Data files (`data/`) are no longer tracked in git; generated entirely by `prep_data.py`
- Removed standalone helper scripts (`inspect_119.py`, `convert_2025.py`, `merge_districts.py`); their logic is consolidated in `prep_data.py`

#### Added
- Vacancy labels for districts with no current representative (CA-1, NJ-11), showing reason and special election date
- Manual legislator override system in `prep_data.py` for seats missing from upstream data (GA-14 Clay Fuller, CA-1 and NJ-11 vacancies)
- `.gitignore` for `data/`, `.idea/`, and Python bytecode

### [1.1.0] - 2026-04-11
#### Changed
- District data updated from 118th to 119th Congress boundaries
- `prep_data.py` now produces both `congressional_districts_119.geojson` (current) and `congressional_districts.geojson` (2026 expected with redistricting)
- Census TIGER ZIP is cached locally after first download and reused on subsequent runs

#### Added
- Toggle in the state sidebar to switch between "Current Districts" (119th Congress) and "2026 Expected" (with 2025 redistricting for CA, MO, NC, OH, TX, UT)

### [1.0.0] - 2026-03-28
#### Added
- Interactive US map with 2024 Presidential Election results by state
- Congressional district boundaries (118th Congress)
- Sidebar with U.S. Senators and voter registration links per state
- Representative and Ballotpedia 2026 candidate links per congressional district
- Inset maps for Alaska and Hawaii
- Local HTTP server (`serve.py`) with auto-launch
- Data preparation script (`scripts/prep_data.py`) for downloading Census and legislator data

## GitHub Pages

To deploy on GitHub Pages, the generated `data/` files must be committed (or served separately). Run `prep_data.py` first, then commit the `data/` directory for that deployment branch. The app requires no build step beyond data generation.
