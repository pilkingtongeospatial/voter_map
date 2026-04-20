"""
Static data constants for the voter map pipeline.

No logic lives here. Each constant is imported by transforms.py (pure
transformations) or prep_data.py (the orchestrator).
"""

# ── 2024 election results (Trump=R, Harris=D) ─────────────────────────────────

ELECTION_2024 = {
    "AL": "R", "AK": "R", "AZ": "R", "AR": "R", "CA": "D", "CO": "D", "CT": "D", "DE": "D",
    "FL": "R", "GA": "R", "HI": "D", "ID": "R", "IL": "D", "IN": "R", "IA": "R", "KS": "R",
    "KY": "R", "LA": "R", "ME": "D", "MD": "D", "MA": "D", "MI": "R", "MN": "D", "MS": "R",
    "MO": "R", "MT": "R", "NE": "R", "NV": "R", "NH": "D", "NJ": "D", "NM": "D", "NY": "D",
    "NC": "R", "ND": "R", "OH": "R", "OK": "R", "OR": "D", "PA": "R", "RI": "D", "SC": "R",
    "SD": "R", "TN": "R", "TX": "R", "UT": "R", "VT": "D", "VA": "D", "WA": "D", "WV": "R",
    "WI": "R", "WY": "R",
}

# ── voter registration links ──────────────────────────────────────────────────

VOTER_REG = {
    "AL": {"url": "https://www.sos.alabama.gov/alabama-votes/voter/register-to-vote", "name": "Alabama Voter Registration"},
    "AK": {"url": "https://voterregistration.alaska.gov/", "name": "Alaska Voter Registration"},
    "AZ": {"url": "https://servicearizona.com/VoterRegistration/", "name": "Arizona Voter Registration"},
    "AR": {"url": "https://www.sos.arkansas.gov/elections/voter-information/voter-registration", "name": "Arkansas Voter Registration"},
    "CA": {"url": "https://registertovote.ca.gov/", "name": "California Voter Registration"},
    "CO": {"url": "https://www.sos.state.co.us/voter/", "name": "Colorado Voter Registration"},
    "CT": {"url": "https://voterregistration.ct.gov/OLVR/welcome.do", "name": "Connecticut Voter Registration"},
    "DE": {"url": "https://ivote.de.gov/VoterView/registrant/newregistrant", "name": "Delaware Voter Registration"},
    "FL": {"url": "https://registertovoteflorida.gov/", "name": "Florida Voter Registration"},
    "GA": {"url": "https://mvp.sos.ga.gov/s/voter-registration", "name": "Georgia Voter Registration"},
    "HI": {"url": "https://olvr.hawaii.gov/", "name": "Hawaii Voter Registration"},
    "ID": {"url": "https://idahovotes.gov/", "name": "Idaho Voter Registration"},
    "IL": {"url": "https://ova.elections.il.gov/", "name": "Illinois Voter Registration"},
    "IN": {"url": "https://indianavoters.in.gov/", "name": "Indiana Voter Registration"},
    "IA": {"url": "https://sos.iowa.gov/elections/voterinformation/voterregistration.html", "name": "Iowa Voter Registration"},
    "KS": {"url": "https://www.kdor.ks.gov/Apps/VoterReg/Default.aspx", "name": "Kansas Voter Registration"},
    "KY": {"url": "https://vrsws.sos.ky.gov/ovrweb/", "name": "Kentucky Voter Registration"},
    "LA": {"url": "https://voterportal.sos.la.gov/Voter-Registration/Register", "name": "Louisiana Voter Registration"},
    "ME": {"url": "https://www.maine.gov/sos/cec/elec/voter-info/votereg.html", "name": "Maine Voter Registration"},
    "MD": {"url": "https://voterservices.elections.maryland.gov/OnlineVoterRegistration/InstructionsStep1", "name": "Maryland Voter Registration"},
    "MA": {"url": "https://www.sec.state.ma.us/OVR/", "name": "Massachusetts Voter Registration"},
    "MI": {"url": "https://mvic.sos.state.mi.us/RegisterVoter", "name": "Michigan Voter Registration"},
    "MN": {"url": "https://mnvotes.sos.state.mn.us/VoterRegistration/VoterRegistrationMain.aspx", "name": "Minnesota Voter Registration"},
    "MS": {"url": "https://www.sos.ms.gov/voter-registration-information", "name": "Mississippi Voter Registration"},
    "MO": {"url": "https://www.sos.mo.gov/elections/goVoteMissouri/register.aspx", "name": "Missouri Voter Registration"},
    "MT": {"url": "https://sosmt.gov/elections/vote/", "name": "Montana Voter Registration"},
    "NE": {"url": "https://www.nebraska.gov/apps-sos-voter-registration/", "name": "Nebraska Voter Registration"},
    "NV": {"url": "https://www.nvsos.gov/sos/elections/voters", "name": "Nevada Voter Registration"},
    "NH": {"url": "https://www.sos.nh.gov/elections/voters/register-vote", "name": "New Hampshire Voter Registration"},
    "NJ": {"url": "https://voter.svrs.nj.gov/register", "name": "New Jersey Voter Registration"},
    "NM": {"url": "https://www.sos.nm.gov/voting-and-elections/voter-information-portal/voter-registration-information/", "name": "New Mexico Voter Registration"},
    "NY": {"url": "https://www.elections.ny.gov/VoterRegister.html", "name": "New York Voter Registration"},
    "NC": {"url": "https://www.ncsbe.gov/registering", "name": "North Carolina Voter Registration"},
    "ND": {"url": "https://vip.sos.nd.gov/PortalList.aspx", "name": "North Dakota Voter Registration"},
    "OH": {"url": "https://olvr.ohiosos.gov/", "name": "Ohio Voter Registration"},
    "OK": {"url": "https://www.elections.ok.gov/", "name": "Oklahoma Voter Registration"},
    "OR": {"url": "https://sos.oregon.gov/voting/pages/register.aspx", "name": "Oregon Voter Registration"},
    "PA": {"url": "https://www.vote.pa.gov/Register-to-Vote/Pages/default.aspx", "name": "Pennsylvania Voter Registration"},
    "RI": {"url": "https://vote.sos.ri.gov/Voter/RegisterToVote", "name": "Rhode Island Voter Registration"},
    "SC": {"url": "https://www.scvotes.gov/voter-registration", "name": "South Carolina Voter Registration"},
    "SD": {"url": "https://sdsos.gov/elections-voting/voting/register-to-vote.aspx", "name": "South Dakota Voter Registration"},
    "TN": {"url": "https://ovr.govote.tn.gov/", "name": "Tennessee Voter Registration"},
    "TX": {"url": "https://www.votetexas.gov/register-to-vote/", "name": "Texas Voter Registration"},
    "UT": {"url": "https://vote.utah.gov/", "name": "Utah Voter Registration"},
    "VT": {"url": "https://olvr.vermont.gov/", "name": "Vermont Voter Registration"},
    "VA": {"url": "https://www.elections.virginia.gov/registration/", "name": "Virginia Voter Registration"},
    "WA": {"url": "https://www.sos.wa.gov/elections/register.aspx", "name": "Washington Voter Registration"},
    "WV": {"url": "https://ovr.sos.wv.gov/Register/Landing", "name": "West Virginia Voter Registration"},
    "WI": {"url": "https://myvote.wi.gov/en-us/Register-To-Vote", "name": "Wisconsin Voter Registration"},
    "WY": {"url": "https://sos.wyo.gov/Elections/", "name": "Wyoming Voter Registration"},
}

# ── 2025 redistricting metadata ───────────────────────────────────────────────
# Maps FIPS code -> (state abbr, local zip filename, download URL)
# Source: American Redistricting Project (thearp.org)

REDISTRICTED = {
    "06": ("CA", "CA_CD_2025.zip", "https://thearp.org/documents/19013/ca_cd_prop50_EnhHRHd.zip"),
    "29": ("MO", "MO_CD_2025.zip", "https://thearp.org/documents/18733/MO_CD_MO_2025.zip"),
    "37": ("NC", "NC_CD_2025.zip", "https://thearp.org/documents/18957/nc_cd_2025.zip"),
    "39": ("OH", "OH_CD_2025.zip", "https://thearp.org/documents/18960/OH_CD_10302025.zip"),
    "48": ("TX", "TX_CD_2025.zip", "https://thearp.org/documents/18577/tx_cd_Enacted_2025.zip"),
    "49": ("UT", "UT_CD_2025.zip", "https://thearp.org/documents/19051/UT_CD_CourtOrdered11112025.zip"),
}

# ── state name <-> abbr lookup ────────────────────────────────────────────────

STATE_NAME_TO_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI",
    "Wyoming": "WY",
}

# Inverted lookup (computed once at module load)
ABBR_TO_STATE_NAME = {abbr: name for name, abbr in STATE_NAME_TO_ABBR.items()}

# ── manual legislator overrides (for seats missing from upstream data) ───────
# Applied only when upstream `congress-legislators` has not yet filled the seat.

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
