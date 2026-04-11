"""
Voter Map Data Preparation Script
Downloads and processes all data needed for the US Voter Information Map.

Produces:
  data/states.geojson                        State boundaries + 2024 election results
  data/congressional_districts_119.geojson   119th Congress district boundaries (current)
  data/congressional_districts.geojson       2026 expected districts (119th + 2025 redistricting)
  data/legislators.json                      Current legislators by state
  data/state_meta.json                       Voter registration links + election results

Note: 2025 redistricting ZIP files for CA, MO, NC, OH, TX, UT are not auto-downloaded
(they come from individual state redistricting bodies). Place them manually in
data/redistricting_2025/ before running. If absent, both district files will use
the 119th Congress boundaries.
"""

import os
import sys
import json
import zipfile
import io
import shutil
import urllib.request
import subprocess

# ── helpers ──────────────────────────────────────────────────────────────────

def pip_install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])

def download(url, label):
    print(f"  Downloading {label}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=120).read()

try:
    import shapefile
except ImportError:
    print("Installing pyshp...")
    pip_install("pyshp")
    import shapefile

try:
    import yaml
except ImportError:
    print("Installing pyyaml...")
    pip_install("pyyaml")
    import yaml

# ── paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SCRIPT_DIR)
DATA_DIR   = os.path.join(ROOT_DIR, "data")
REDIST_DIR = os.path.join(DATA_DIR, "redistricting_2025")
os.makedirs(DATA_DIR, exist_ok=True)

# ── 2024 election results (Trump=R, Harris=D) ─────────────────────────────────

ELECTION_2024 = {
    "AL":"R","AK":"R","AZ":"R","AR":"R","CA":"D","CO":"D","CT":"D","DE":"D",
    "FL":"R","GA":"R","HI":"D","ID":"R","IL":"D","IN":"R","IA":"R","KS":"R",
    "KY":"R","LA":"R","ME":"D","MD":"D","MA":"D","MI":"R","MN":"D","MS":"R",
    "MO":"R","MT":"R","NE":"R","NV":"R","NH":"D","NJ":"D","NM":"D","NY":"D",
    "NC":"R","ND":"R","OH":"R","OK":"R","OR":"D","PA":"R","RI":"D","SC":"R",
    "SD":"R","TN":"R","TX":"R","UT":"R","VT":"D","VA":"D","WA":"D","WV":"R",
    "WI":"R","WY":"R",
}

# ── voter registration links ──────────────────────────────────────────────────

VOTER_REG = {
    "AL":{"url":"https://www.sos.alabama.gov/alabama-votes/voter/register-to-vote","name":"Alabama Voter Registration"},
    "AK":{"url":"https://voterregistration.alaska.gov/","name":"Alaska Voter Registration"},
    "AZ":{"url":"https://servicearizona.com/VoterRegistration/","name":"Arizona Voter Registration"},
    "AR":{"url":"https://www.sos.arkansas.gov/elections/voter-information/voter-registration","name":"Arkansas Voter Registration"},
    "CA":{"url":"https://registertovote.ca.gov/","name":"California Voter Registration"},
    "CO":{"url":"https://www.sos.state.co.us/voter/","name":"Colorado Voter Registration"},
    "CT":{"url":"https://voterregistration.ct.gov/OLVR/welcome.do","name":"Connecticut Voter Registration"},
    "DE":{"url":"https://ivote.de.gov/VoterView/registrant/newregistrant","name":"Delaware Voter Registration"},
    "FL":{"url":"https://registertovoteflorida.gov/","name":"Florida Voter Registration"},
    "GA":{"url":"https://mvp.sos.ga.gov/s/voter-registration","name":"Georgia Voter Registration"},
    "HI":{"url":"https://olvr.hawaii.gov/","name":"Hawaii Voter Registration"},
    "ID":{"url":"https://idahovotes.gov/","name":"Idaho Voter Registration"},
    "IL":{"url":"https://ova.elections.il.gov/","name":"Illinois Voter Registration"},
    "IN":{"url":"https://indianavoters.in.gov/","name":"Indiana Voter Registration"},
    "IA":{"url":"https://sos.iowa.gov/elections/voterinformation/voterregistration.html","name":"Iowa Voter Registration"},
    "KS":{"url":"https://www.kdor.ks.gov/Apps/VoterReg/Default.aspx","name":"Kansas Voter Registration"},
    "KY":{"url":"https://vrsws.sos.ky.gov/ovrweb/","name":"Kentucky Voter Registration"},
    "LA":{"url":"https://voterportal.sos.la.gov/Voter-Registration/Register","name":"Louisiana Voter Registration"},
    "ME":{"url":"https://www.maine.gov/sos/cec/elec/voter-info/votereg.html","name":"Maine Voter Registration"},
    "MD":{"url":"https://voterservices.elections.maryland.gov/OnlineVoterRegistration/InstructionsStep1","name":"Maryland Voter Registration"},
    "MA":{"url":"https://www.sec.state.ma.us/OVR/","name":"Massachusetts Voter Registration"},
    "MI":{"url":"https://mvic.sos.state.mi.us/RegisterVoter","name":"Michigan Voter Registration"},
    "MN":{"url":"https://mnvotes.sos.state.mn.us/VoterRegistration/VoterRegistrationMain.aspx","name":"Minnesota Voter Registration"},
    "MS":{"url":"https://www.sos.ms.gov/voter-registration-information","name":"Mississippi Voter Registration"},
    "MO":{"url":"https://www.sos.mo.gov/elections/goVoteMissouri/register.aspx","name":"Missouri Voter Registration"},
    "MT":{"url":"https://sosmt.gov/elections/vote/","name":"Montana Voter Registration"},
    "NE":{"url":"https://www.nebraska.gov/apps-sos-voter-registration/","name":"Nebraska Voter Registration"},
    "NV":{"url":"https://www.nvsos.gov/sos/elections/voters","name":"Nevada Voter Registration"},
    "NH":{"url":"https://www.sos.nh.gov/elections/voters/register-vote","name":"New Hampshire Voter Registration"},
    "NJ":{"url":"https://voter.svrs.nj.gov/register","name":"New Jersey Voter Registration"},
    "NM":{"url":"https://www.sos.nm.gov/voting-and-elections/voter-information-portal/voter-registration-information/","name":"New Mexico Voter Registration"},
    "NY":{"url":"https://www.elections.ny.gov/VoterRegister.html","name":"New York Voter Registration"},
    "NC":{"url":"https://www.ncsbe.gov/registering","name":"North Carolina Voter Registration"},
    "ND":{"url":"https://vip.sos.nd.gov/PortalList.aspx","name":"North Dakota Voter Registration"},
    "OH":{"url":"https://olvr.ohiosos.gov/","name":"Ohio Voter Registration"},
    "OK":{"url":"https://www.elections.ok.gov/","name":"Oklahoma Voter Registration"},
    "OR":{"url":"https://sos.oregon.gov/voting/pages/register.aspx","name":"Oregon Voter Registration"},
    "PA":{"url":"https://www.vote.pa.gov/Register-to-Vote/Pages/default.aspx","name":"Pennsylvania Voter Registration"},
    "RI":{"url":"https://vote.sos.ri.gov/Voter/RegisterToVote","name":"Rhode Island Voter Registration"},
    "SC":{"url":"https://www.scvotes.gov/voter-registration","name":"South Carolina Voter Registration"},
    "SD":{"url":"https://sdsos.gov/elections-voting/voting/register-to-vote.aspx","name":"South Dakota Voter Registration"},
    "TN":{"url":"https://ovr.govote.tn.gov/","name":"Tennessee Voter Registration"},
    "TX":{"url":"https://www.votetexas.gov/register-to-vote/","name":"Texas Voter Registration"},
    "UT":{"url":"https://vote.utah.gov/","name":"Utah Voter Registration"},
    "VT":{"url":"https://olvr.vermont.gov/","name":"Vermont Voter Registration"},
    "VA":{"url":"https://www.elections.virginia.gov/registration/","name":"Virginia Voter Registration"},
    "WA":{"url":"https://www.sos.wa.gov/elections/register.aspx","name":"Washington Voter Registration"},
    "WV":{"url":"https://ovr.sos.wv.gov/Register/Landing","name":"West Virginia Voter Registration"},
    "WI":{"url":"https://myvote.wi.gov/en-us/Register-To-Vote","name":"Wisconsin Voter Registration"},
    "WY":{"url":"https://sos.wyo.gov/Elections/","name":"Wyoming Voter Registration"},
}

# ── 2025 redistricting metadata ───────────────────────────────────────────────
# Maps FIPS code -> (state abbr, zip filename, shapefile base name inside zip)

REDISTRICTED = {
    "06": ("CA", "CA_CD_2025.zip", "CA_CD_Prop50"),
    "29": ("MO", "MO_CD_2025.zip", "MO_CD_MO_First_2025"),
    "37": ("NC", "NC_CD_2025.zip", "NC_CD_2025"),
    "39": ("OH", "OH_CD_2025.zip", "OH_CD_10302025"),
    "48": ("TX", "TX_CD_2025.zip", "TX_CD_PlanC2333"),
    "49": ("UT", "UT_CD_2025.zip", "UT_CD_CourtOrdered11112025"),
}

# ── 1. State boundaries ───────────────────────────────────────────────────────

print("\n[1/5] State boundaries")
states_path = os.path.join(DATA_DIR, "states.geojson")
states_url = (
    "https://raw.githubusercontent.com/PublicaMundi/MappingAPI"
    "/master/data/geojson/us-states.json"
)
raw = download(states_url, "states GeoJSON")

STATE_NAME_TO_ABBR = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
    "Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA",
    "Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA",
    "Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD",
    "Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS",
    "Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV",
    "New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY",
    "North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK",
    "Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC",
    "South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT",
    "Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI",
    "Wyoming":"WY",
}
states_data = json.loads(raw)
for feat in states_data["features"]:
    name = feat["properties"].get("name", "")
    abbr = STATE_NAME_TO_ABBR.get(name, "")
    feat["properties"]["abbr"]  = abbr
    feat["properties"]["party"] = ELECTION_2024.get(abbr, "")
with open(states_path, "w") as f:
    json.dump(states_data, f)
print(f"  Saved {len(states_data['features'])} state features -> data/states.geojson")

# ── 2. 119th Congress district boundaries (current) ──────────────────────────

print("\n[2/5] 119th Congress district boundaries (current representation)")
cd119_path  = os.path.join(DATA_DIR, "congressional_districts_119.geojson")
local_zip   = os.path.join(DATA_DIR, "cb_2024_us_cd119_500k.zip")
cd119_url   = "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_cd119_500k.zip"
shp_base    = "cb_2024_us_cd119_500k"

if os.path.exists(local_zip):
    print(f"  Using cached zip: {os.path.relpath(local_zip, ROOT_DIR)}")
    zip_bytes = open(local_zip, "rb").read()
else:
    zip_bytes = download(cd119_url, "Census TIGER 119th Congress ZIP (~16 MB)")
    with open(local_zip, "wb") as f:
        f.write(zip_bytes)
    print(f"  Cached to {os.path.relpath(local_zip, ROOT_DIR)}")

print("  Converting shapefile -> GeoJSON...")
with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
    shp = io.BytesIO(z.read(f"{shp_base}.shp"))
    dbf = io.BytesIO(z.read(f"{shp_base}.dbf"))
    shx = io.BytesIO(z.read(f"{shp_base}.shx"))
    sf  = shapefile.Reader(shp=shp, dbf=dbf, shx=shx)
    cd119_gj = sf.__geo_interface__

with open(cd119_path, "w") as f:
    json.dump(cd119_gj, f)
print(f"  Saved {len(cd119_gj['features'])} district features -> data/congressional_districts_119.geojson")

# ── 3. 2026 expected districts (119th + 2025 redistricting) ──────────────────

print("\n[3/5] 2026 expected districts")
cd_path = os.path.join(DATA_DIR, "congressional_districts.geojson")

# Determine which redistricting zips are available
available = {
    fips: meta for fips, meta in REDISTRICTED.items()
    if os.path.exists(os.path.join(REDIST_DIR, meta[1]))
}

if not available:
    print("  No redistricting ZIPs found in data/redistricting_2025/")
    print("  Copying 119th Congress file as the 2026 baseline.")
    shutil.copy(cd119_path, cd_path)
    print(f"  Saved -> data/congressional_districts.geojson")
else:
    print(f"  Redistricting data found for: {', '.join(v[0] for v in available.values())}")

    # Filter out redistricted states from the 119th base
    kept = [f for f in cd119_gj["features"]
            if f["properties"].get("STATEFP", "") not in available]
    print(f"  Kept {len(kept)} features from non-redistricted states")

    # Convert and normalize each redistricting shapefile
    new_features = []
    for fips in sorted(available):
        abbr, zip_name, shp_base_r = available[fips]
        zip_path = os.path.join(REDIST_DIR, zip_name)

        with zipfile.ZipFile(zip_path) as z:
            names    = z.namelist()
            shp_name = next(n for n in names if n.lower() == f"{shp_base_r.lower()}.shp")
            dbf_name = next(n for n in names if n.lower() == f"{shp_base_r.lower()}.dbf")
            shx_name = next(n for n in names if n.lower() == f"{shp_base_r.lower()}.shx")
            shp = io.BytesIO(z.read(shp_name))
            dbf = io.BytesIO(z.read(dbf_name))
            shx = io.BytesIO(z.read(shx_name))

        sf  = shapefile.Reader(shp=shp, dbf=dbf, shx=shx)
        gj  = sf.__geo_interface__

        for feat in gj["features"]:
            props    = feat["properties"]
            dist_num = str(int(props.get("DISTRICT", "0")))
            feat["properties"] = {
                "STATEFP":  props.get("ST", fips),
                "CD119FP":  dist_num.zfill(2),
                "NAMELSAD": props.get("DIST_NAME", f"Congressional District {dist_num}"),
                "GEOID":    props.get("ST", fips) + dist_num.zfill(2),
                "CDSESSN":  "119",
                "SOURCE":   "redistricting_2025",
            }
            new_features.append(feat)

        print(f"  {abbr}: {len(gj['features'])} redistricted districts")

    combined = kept + new_features
    out = {"type": "FeatureCollection", "features": combined}
    with open(cd_path, "w") as f:
        json.dump(out, f)
    print(f"  Saved {len(combined)} total features -> data/congressional_districts.geojson")
    print(f"  ({len(kept)} unchanged + {len(new_features)} redistricted)")

# ── 4. Current legislators ────────────────────────────────────────────────────

print("\n[4/5] Current legislators")
leg_url = (
    "https://raw.githubusercontent.com/unitedstates/congress-legislators"
    "/main/legislators-current.yaml"
)
leg_raw     = download(leg_url, "legislators-current.yaml")
legislators = yaml.safe_load(leg_raw)

by_state = {}
for leg in legislators:
    terms = leg.get("terms", [])
    if not terms:
        continue
    term  = terms[-1]
    state = term.get("state", "")
    typ   = term.get("type", "")
    party = term.get("party", "Unknown")
    url   = term.get("url", "") or ""
    name_d = leg.get("name", {})
    full  = name_d.get("official_full", "") or f"{name_d.get('first','')} {name_d.get('last','')}".strip()

    if state not in by_state:
        by_state[state] = {"senators": [], "representatives": {}}

    info = {"name": full, "party": party, "url": url}

    if typ == "sen":
        by_state[state]["senators"].append(info)
    elif typ == "rep":
        district = term.get("district", 0) or 0
        by_state[state]["representatives"][str(district)] = info

# ── manual overrides (vacancies & missing data from upstream) ──────────────

MANUAL_REPS = {
    # Clay Fuller won GA-14 special election April 7, 2026; upstream YAML lags
    ("GA", "14"): {
        "name": "Clay Fuller", "party": "Republican",
        "url": "https://fuller.house.gov",
    },
    # Doug LaMalfa (R) died January 6, 2026
    ("CA", "1"): {
        "name": "Vacant", "party": "", "url": "",
        "vacant": True,
        "vacancy_reason": "Rep. Doug LaMalfa (R) died January 6, 2026. Special election August 4, 2026.",
    },
    # Mikie Sherrill (D) resigned November 20, 2025 (won NJ governor's race)
    ("NJ", "11"): {
        "name": "Vacant", "party": "", "url": "",
        "vacant": True,
        "vacancy_reason": "Rep. Mikie Sherrill (D) resigned November 20, 2025. Special election April 16, 2026.",
    },
}

applied = 0
for (state, dist), info in MANUAL_REPS.items():
    if state not in by_state:
        by_state[state] = {"senators": [], "representatives": {}}
    # Only apply if upstream didn't already fill this seat
    if dist not in by_state[state]["representatives"]:
        by_state[state]["representatives"][dist] = info
        label = info["name"]
        print(f"  Applied override: {state}-{dist} -> {label}")
        applied += 1
if applied:
    print(f"  ({applied} override(s) applied)")
else:
    print("  No overrides needed (all seats filled by upstream data)")

leg_path = os.path.join(DATA_DIR, "legislators.json")
with open(leg_path, "w") as f:
    json.dump(by_state, f, indent=2)
print(f"  Saved {len(by_state)} states -> data/legislators.json")

# ── 5. Voter registration + election results ──────────────────────────────────

print("\n[5/5] Voter registration links & election results")
meta_path = os.path.join(DATA_DIR, "state_meta.json")
meta = {}
for abbr, reg in VOTER_REG.items():
    meta[abbr] = {
        "voter_reg": reg,
        "party": ELECTION_2024.get(abbr, ""),
    }
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
print(f"  Saved metadata for {len(meta)} states -> data/state_meta.json")

# ── summary ───────────────────────────────────────────────────────────────────

print("\nAll data preparation complete!")
print(f"Data directory: {DATA_DIR}")
print()
print("Files produced:")
for name in [
    "states.geojson",
    "congressional_districts_119.geojson",
    "congressional_districts.geojson",
    "legislators.json",
    "state_meta.json",
]:
    path = os.path.join(DATA_DIR, name)
    if os.path.exists(path):
        size_mb = os.path.getsize(path) / 1_048_576
        print(f"  {name:<45} {size_mb:6.1f} MB")
