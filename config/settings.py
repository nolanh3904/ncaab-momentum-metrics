# config/settings.py

# ── API ──────────────────────────────────────────────────────────────────────
ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball"

# Rate limiting (requests per second)
RATE_LIMIT = 20

# ── Season ───────────────────────────────────────────────────────────────────
SEASON_START = "2025-11-04"
SEASON_END   = "2026-04-04"

# ── File Paths ────────────────────────────────────────────────────────────────
import os
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR        = os.path.join(BASE_DIR, "data", "raw")
OUTPUT_DIR     = os.path.join(BASE_DIR, "data", "outputs")

for _dir in (RAW_DIR, OUTPUT_DIR):
    os.makedirs(_dir, exist_ok=True)

# ── Run Detection ─────────────────────────────────────────────────────────────
# Minimum points to count as a "run"
MIN_RUN_SIZE = 4

# ── 2026 Tournament Seed Lookup ───────────────────────────────────────────────
# Used as the tournament team source and to weight games by opponent quality
#Update Teams before each tournament
TEAM_SEEDS_2026 = {
    # EAST
    "Duke Blue Devils":           1,
    "Siena Saints":               16,
    "Ohio State Buckeyes":        8,
    "TCU Horned Frogs":           9,
    "St. John's Red Storm":       5,
    "Northern Iowa Panthers":     12,
    "Kansas Jayhawks":            4,
    "California Baptist Lancers": 13,
    "Louisville Cardinals":       6,
    "South Florida Bulls":        11,
    "Michigan State Spartans":    3,
    "North Dakota State Bison":   14,
    "UCLA Bruins":                7,
    "UCF Knights":                10,
    "UConn Huskies":              2,
    "Furman Paladins":            15,
    # SOUTH
    "Florida Gators":             1,
    "Prairie View A&M Panthers":  16,
    "Clemson Tigers":             8,
    "Iowa Hawkeyes":              9,
    "Vanderbilt Commodores":      5,
    "McNeese Cowboys":            12,
    "Nebraska Cornhuskers":       4,
    "Troy Trojans":               13,
    "North Carolina Tar Heels":   6,
    "VCU Rams":                   11,
    "Illinois Fighting Illini":   3,
    "Pennsylvania Quakers":       14,
    "Saint Mary's Gaels":         7,
    "Texas A&M Aggies":           10,
    "Houston Cougars":            2,
    "Idaho Vandals":              15,
    # WEST
    "Arizona Wildcats":           1,
    "Long Island University Sharks": 16,
    "Villanova Wildcats":         8,
    "Utah State Aggies":          9,
    "Wisconsin Badgers":          5,
    "High Point Panthers":        12,
    "Arkansas Razorbacks":        4,
    "Hawai'i Rainbow Warriors":   13,
    "BYU Cougars":                6,
    "Texas Longhorns":            11,
    "Gonzaga Bulldogs":           3,
    "Kennesaw State Owls":        14,
    "Miami Hurricanes":           7,
    "Missouri Tigers":            10,
    "Purdue Boilermakers":        2,
    "Queens University Royals":   15,
    # MIDWEST
    "Michigan Wolverines":        1,
    "Howard Bison":               16,
    "Georgia Bulldogs":           8,
    "Saint Louis Billikens":      9,
    "Texas Tech Red Raiders":     5,
    "Akron Zips":                 12,
    "Alabama Crimson Tide":       4,
    "Hofstra Pride":              13,
    "Tennessee Volunteers":       6,
    "Miami (OH) RedHawks":        11,
    "Virginia Cavaliers":         3,
    "Wright State Raiders":       14,
    "Kentucky Wildcats":          7,
    "Santa Clara Broncos":        10,
    "Iowa State Cyclones":        2,
    "Tennessee State Tigers":     15,
}

# Tournament membership derived from the seed lookup to keep names consistent.
MARCH_MADNESS_2026 = set(TEAM_SEEDS_2026)

# Seed weights
SEED_WEIGHTS = {
    1:  1.00,
    2:  0.94,
    3:  0.88,
    4:  0.81,
    5:  0.75,
    6:  0.69,
    7:  0.63,
    8:  0.56,
    9:  0.50,
    10: 0.44,
    11: 0.38,
    12: 0.31,
    13: 0.25,
    14: 0.19,
    15: 0.13,
    16: 0.06,
}
