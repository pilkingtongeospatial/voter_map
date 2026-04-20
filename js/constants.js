// Static data constants for the voter map client.
// No logic lives here. Every export is a frozen-in-spirit lookup table.

export const PARTY_COLOR = { R: "#c0392b", D: "#2471a3" };

export const PARTY_LABEL = {
  R: "Republican",
  D: "Democrat",
  Independent: "Independent",
};

export const FIPS_TO_ABBR = {
  "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT",
  "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL",
  "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
  "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE",
  "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
  "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
  "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV",
  "55": "WI", "56": "WY"
};

// Precomputed reverse lookup (avoids O(n) .find() scans in the hot path).
export const ABBR_TO_FIPS = Object.fromEntries(
  Object.entries(FIPS_TO_ABBR).map(([fips, abbr]) => [abbr, fips])
);

export const STATE_CENTROIDS = {
  "AL": [32.806, -86.791], "AK": [64.2, -153.0], "AZ": [34.048, -111.093],
  "AR": [34.969, -92.373], "CA": [36.778, -119.418], "CO": [39.113, -105.358],
  "CT": [41.598, -72.755], "DE": [39.318, -75.507], "FL": [27.994, -81.760],
  "GA": [32.678, -83.223], "HI": [20.798, -156.331], "ID": [44.068, -114.742],
  "IL": [40.349, -88.986], "IN": [39.849, -86.258], "IA": [42.011, -93.210],
  "KS": [38.526, -96.726], "KY": [37.668, -84.670], "LA": [31.169, -91.867],
  "ME": [44.693, -69.381], "MD": [39.063, -76.802], "MA": [42.230, -71.530],
  "MI": [44.314, -85.602], "MN": [46.392, -94.636], "MS": [32.741, -89.678],
  "MO": [38.456, -92.288], "MT": [46.921, -110.454], "NE": [41.492, -99.901],
  "NV": [38.802, -116.419], "NH": [43.193, -71.572], "NJ": [40.058, -74.405],
  "NM": [34.307, -106.018], "NY": [42.165, -74.948], "NC": [35.782, -80.793],
  "ND": [47.528, -99.784], "OH": [40.388, -82.764], "OK": [35.565, -96.928],
  "OR": [43.804, -120.554], "PA": [41.203, -77.194], "RI": [41.742, -71.477],
  "SC": [33.836, -81.163], "SD": [44.299, -99.438], "TN": [35.517, -86.580],
  "TX": [31.054, -97.563], "UT": [39.320, -111.093], "VT": [44.558, -72.577],
  "VA": [37.431, -78.656], "WA": [47.400, -121.490], "WV": [38.491, -80.954],
  "WI": [43.784, -88.787], "WY": [43.075, -107.290]
};

// State abbrs -> full name, underscore-escaped for URL building (e.g. Ballotpedia).
export const ABBR_TO_BALLOTPEDIA_STATE = {
  "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
  "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
  "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
  "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
  "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
  "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
  "NH": "New_Hampshire", "NJ": "New_Jersey", "NM": "New_Mexico", "NY": "New_York",
  "NC": "North_Carolina", "ND": "North_Dakota", "OH": "Ohio", "OK": "Oklahoma",
  "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode_Island", "SC": "South_Carolina",
  "SD": "South_Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
  "VA": "Virginia", "WA": "Washington", "WV": "West_Virginia", "WI": "Wisconsin",
  "WY": "Wyoming"
};
