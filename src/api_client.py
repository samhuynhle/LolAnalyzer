import requests
import time
from urllib.parse import quote

class RiotApiClient:
    def __init__(self, api_key, routing_region):
        self.api_key = api_key
        self.routing = routing_region
        self.base_url = f"https://{routing_region}.api.riotgames.com"
        self.headers = {"X-Riot-Token": api_key}

    def get(self, endpoint, base_url=None):
        url = f"{base_url or self.base_url}{endpoint}"
        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            if response.status_code == 404 or response.status_code == 403:
                return None
            response.raise_for_status()
            return response.json()

    def discover_region(self, name, tag):
        """Attempts to find the player across major Riot routing regions."""
        regions = ["europe", "americas", "asia"]
        endpoint = f"/riot/account/v1/accounts/by-riot-id/{quote(name)}/{tag}"

        print(f"Searching for {name}#{tag} across all regions...")
        for region in regions:
            base_url = f"https://{region}.api.riotgames.com"
            data = self.get(endpoint, base_url=base_url)
            if data and "puuid" in data:
                print(f"Player found in {region.upper()}!")
                return region, data["puuid"]
        return None, None

    def get_puuid(self, name, tag):

        endpoint = f"/riot/account/v1/accounts/by-riot-id/{quote(name)}/{tag}"
        return self.get(endpoint)["puuid"]

    def get_match_ids(self, puuid, count, queue=None):
        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
        if queue:
            endpoint += f"&queue={queue}"
        return self.get(endpoint)

    def get_match_details(self, match_id):
        endpoint = f"/lol/match/v5/matches/{match_id}"
        return self.get(endpoint)
