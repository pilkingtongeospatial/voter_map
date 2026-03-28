"""
Voter Map Data Preparation Script
Downloads and processes all data needed for the US Voter Information Map.
"""

import os
import sys
import json
import zipfile
import io
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

# ── 1. State boundaries ───────────────────────────────────────────────────────

print("\n[1/4] State boundaries")
states_path = os.path.join(DATA_DIR, "states.geojson")
states_url = (
    "https://raw.githubusercontent.com/PublicaMundi/MappingAPI"
    "/master/data/geojson/us-states.json"
)
raw = download(states_url, "states GeoJSON")
# Inject election result and abbreviation into each feature
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
    name = feat["properties"].get("name","")
    abbr = STATE_NAME_TO_ABBR.get(name,"")
    feat["properties"]["abbr"]   = abbr
    feat["properties"]["party"]  = ELECTION_2024.get(abbr,"")
with open(states_path, "w") as f:
    json.dump(states_data, f)
print(f"  Saved {len(states_data['features'])} state features -> data/states.geojson")

# ── 2. Congressional districts ────────────────────────────────────────────────

print("\n[2/4] Congressional district boundaries (118th Congress, 500k scale)")
cd_path = os.path.join(DATA_DIR, "congressional_districts.geojson")
cd_url  = (
    "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_cd118_500k.zip"
)
zip_bytes = download(cd_url, "Census TIGER shapefile ZIP (~5 MB)")

print("  Converting shapefile -> GeoJSON...")
with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
    base = "cb_2022_us_cd118_500k"
    shp  = io.BytesIO(z.read(f"{base}.shp"))
    dbf  = io.BytesIO(z.read(f"{base}.dbf"))
    shx  = io.BytesIO(z.read(f"{base}.shx"))
    sf   = shapefile.Reader(shp=shp, dbf=dbf, shx=shx)
    geojson = sf.__geo_interface__

with open(cd_path, "w") as f:
    json.dump(geojson, f)
print(f"  Saved {len(geojson['features'])} district features -> data/congressional_districts.geojson")

# ── 3. Current legislators ────────────────────────────────────────────────────

print("\n[3/4] Current legislators")
leg_url  = (
    "https://raw.githubusercontent.com/unitedstates/congress-legislators"
    "/main/legislators-current.yaml"
)
leg_raw  = download(leg_url, "legislators-current.yaml")
legislators = yaml.safe_load(leg_raw)

by_state = {}  # { "AL": { "senators": [...], "representatives": { 1: {...}, ... } } }

for leg in legislators:
    terms = leg.get("terms", [])
    if not terms:
        continue
    term  = terms[-1]
    state = term.get("state","")
    typ   = term.get("type","")      # "sen" or "rep"
    party = term.get("party","Unknown")
    url   = term.get("url","") or ""
    name_d = leg.get("name",{})
    full  = name_d.get("official_full","") or f"{name_d.get('first','')} {name_d.get('last','')}".strip()

    if state not in by_state:
        by_state[state] = {"senators":[], "representatives":{}}

    info = {"name": full, "party": party, "url": url}

    if typ == "sen":
        by_state[state]["senators"].append(info)
    elif typ == "rep":
        district = term.get("district", 0) or 0
        by_state[state]["representatives"][str(district)] = info

leg_path = os.path.join(DATA_DIR, "legislators.json")
with open(leg_path, "w") as f:
    json.dump(by_state, f, indent=2)
print(f"  Saved {len(by_state)} states -> data/legislators.json")

# ── 4. Voter registration + election results ──────────────────────────────────

print("\n[4/4] Voter registration links & election results")
meta_path = os.path.join(DATA_DIR, "state_meta.json")
meta = {}
for abbr, reg in VOTER_REG.items():
    meta[abbr] = {
        "voter_reg": reg,
        "party": ELECTION_2024.get(abbr,""),
    }
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
print(f"  Saved metadata for {len(meta)} states -> data/state_meta.json")

print("\nAll data preparation complete!")
print(f"Data directory: {DATA_DIR}")
