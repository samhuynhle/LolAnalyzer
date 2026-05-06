from src.api_client import RiotApiClient
from src.cache_manager import CacheManager
from src.config import get_routing_region

class MatchFetcher:
    def __init__(self, api_key, region=None):
        self.api_key = api_key
        self.region = get_routing_region(region) if region else None
        self.api = RiotApiClient(api_key, self.region or "europe")
        self.cache = None # Player-specific cache
        self.match_cache = None # Global match details cache

    def discover_player(self, name, tag):
        """Resolves PUUID and standardizes the routing region."""
        if not self.region:
            discovered_routing, puuid = self.api.discover_region(name, tag)
            if not discovered_routing:
                return None, None, None
            self.region = discovered_routing
            self.api.routing = discovered_routing
            self.api.base_url = f"https://{discovered_routing}.api.riotgames.com"
        else:
            puuid = self.api.get_puuid(name, tag)
        
        player_slug = f"{name.replace(' ', '_')}-{tag}"
        self.cache = CacheManager(self.region, player_slug)
        self.match_cache = CacheManager(self.region) # Use 'global' subdir
        return self.region, puuid, player_slug

    def fetch_match_ids(self, puuid, count, queue=None):
        cache_id = f"matches_{puuid}_{count}_{queue}"
        match_ids = self.cache.get(cache_id) if self.cache else None
        if not match_ids:
            print(f"Fetching match IDs from API for {puuid}...")
            match_ids = self.api.get_match_ids(puuid, count, queue)
            if self.cache:
                self.cache.save(cache_id, match_ids)
        else:
            print(f"Using cached match IDs for {puuid}.")
        return match_ids

    def fetch_match_details(self, match_id):
        # 1. Check Global Cache
        if self.match_cache:
            cached_detail = self.match_cache.get(match_id)
            if cached_detail:
                return cached_detail
        
        # 2. Fetch from API if not cached
        detail = self.api.get_match_details(match_id)
        
        # 3. Save to Global Cache
        if self.match_cache and detail:
            self.match_cache.save(match_id, detail)
            
        return detail
