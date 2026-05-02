# Constants for the LolAnalyzer project

ROLES = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]

ROLE_MAP = {
    "TOP": "top laner",
    "JUNGLE": "jungler",
    "MIDDLE": "mid laner",
    "BOTTOM": "bot laner",
    "SUPPORT": "support"
}

# Mapping for Riot Regions
AMERICAS = ["NA1", "BR1", "LA1", "LA2"]
ASIA = ["KR", "JP1"]
EUROPE = ["EUW1", "EUNE1", "TR1", "RU"]
SEA = ["OC1", "PH2", "SG2", "TH2", "TW2", "VN2"]

def get_routing_region(region):
    region = region.upper()
    if region in AMERICAS: return "americas"
    if region in ASIA: return "asia"
    if region in EUROPE: return "europe"
    if region in SEA: return "sea"
    return "europe" # Default fallback
