import os
import time
from src.config import ROLES
from src.api_client import RiotApiClient
from src.cache_manager import CacheManager
from src.report_generator import ReportGenerator
from src.data_manager import DataManager

class MatchAnalyzer:
    def __init__(self, api_key, name, tag, region=None, match_count=52):
        self.name = name.strip()
        self.tag = tag.strip()
        self.match_count = match_count
        
        self.validate_inputs()
        
        from src.config import get_routing_region
        # Standardize region to the routing region for consistent folder naming
        self.region = get_routing_region(region) if region else None
        self.api = RiotApiClient(api_key, self.region or "europe")
        
        self.player_slug = f"{self.name.replace(' ', '_')}-{self.tag}"
        self.cache = None # Will be init after discovery
        self.report_gen = None # Will be init after discovery
        self.data_manager = DataManager()
        self.base_results_dir = None

    def validate_inputs(self):
        if len(self.name) < 3 or len(self.name) > 16:
            raise ValueError(f"Invalid Riot Name: '{self.name}'. Must be between 3 and 16 characters.")
        if len(self.tag) < 3 or len(self.tag) > 5:
            raise ValueError(f"Invalid Riot Tag: '{self.tag}'. Must be between 3 and 5 characters.")

    def _get_empty_stats(self):
        return {"team": {"k":[],"d":[],"a":[],"gold":[],"cs":[],"dmg":[]}, 
                "enemy": {"k":[],"d":[],"a":[],"gold":[],"cs":[],"dmg":[]}}

    def run(self, queue=None):
        puuid = None
        
        # Region Discovery Mode
        if not self.region:
            discovered_routing, discovered_puuid = self.api.discover_region(self.name, self.tag)
            if not discovered_routing:
                print(f"Could not find player {self.name}#{self.tag} in any region.")
                return
            self.region = discovered_routing 
            self.api.routing = discovered_routing
            self.api.base_url = f"https://{discovered_routing}.api.riotgames.com"
            puuid = discovered_puuid
        
        # Initialize dependencies that rely on region
        self.cache = CacheManager(self.region, self.player_slug)
        self.report_gen = ReportGenerator(self.name, self.tag, self.region)
        self.base_results_dir = os.path.join("results", self.region, self.player_slug)
        if not os.path.exists(self.base_results_dir):
            os.makedirs(self.base_results_dir)

        if not puuid:
            puuid = self.api.get_puuid(self.name, self.tag)
        
        cache_id = f"matches_{puuid}_{self.match_count}_{queue}"
        match_ids = self.cache.get(cache_id)
        if not match_ids:
            match_ids = self.api.get_match_ids(puuid, self.match_count, queue)
            self.cache.save(cache_id, match_ids)

        data_store = {}
        for prefix in ["PLAYER", "TEAMMATE"]:
            for role in ROLES:
                for outcome in ["WIN", "LOSS"]:
                    data_store[f"{prefix}_{role}_{outcome}"] = self._get_empty_stats()

        processed_count = 0
        detailed_results = []
        print(f"Analyzing {len(match_ids)} matches for {self.name}#{self.tag} ({self.region})...")
        
        for mid in match_ids:
            try:
                time.sleep(0.05)
                m = self.api.get_match_details(mid)
                if m["info"]["gameMode"] != "CLASSIC":
                    continue
                
                p_list = m["info"]["participants"]
                me = next(p for p in p_list if p["puuid"] == puuid)
                team_id = me["teamId"]
                outcome = "WIN" if me["win"] else "LOSS"

                # Capture detailed result for the target player
                detailed_results.append({
                    "match_id": mid,
                    "champion": me["championName"],
                    "role": me["teamPosition"],
                    "win": me["win"],
                    "kills": me["kills"],
                    "deaths": me["deaths"],
                    "assists": me["assists"],
                    "gold": me["goldEarned"],
                    "damage": me["totalDamageDealtToChampions"],
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(m["info"]["gameCreation"]/1000.0))
                })

                found_any_role = False
                for role in ROLES:
                    our_p = self._find_participant(p_list, team_id, role)
                    enemy_p = self._find_participant(p_list, team_id, role, find_enemy=True)

                    if our_p and enemy_p:
                        found_any_role = True
                        prefix = "PLAYER" if our_p["puuid"] == puuid else "TEAMMATE"
                        key = f"{prefix}_{role}_{outcome}"
                        self._record_stats(data_store[key], our_p, enemy_p)
                
                if found_any_role:
                    processed_count += 1

            except Exception as e:
                print(f"Error analyzing match {mid}: {e}")

        if processed_count == 0:
            print(f"\nNo valid CLASSIC matches found for {self.name}#{self.tag}.")
            return

        summary = self.report_gen.generate(match_ids, data_store, processed_count)
        saved_path = self._save_results(summary)
        
        # Register in our NoSQL-style JSON registry with detailed match data
        self.data_manager.register_report(
            self.name, self.tag, self.region, 
            saved_path, self.match_count, processed_count,
            detailed_matches=detailed_results
        )
        
        return summary

    def _find_participant(self, p_list, team_id, role, find_enemy=False):
        target_team = team_id if not find_enemy else (200 if team_id == 100 else 100)
        p = next((p for p in p_list if p["teamId"] == target_team and p["teamPosition"] == role), None)
        if not p and role == "JUNGLE":
            p = next((p for p in p_list if p["teamId"] == target_team and 11 in [p["summoner1Id"], p["summoner2Id"]]), None)
        return p

    def _record_stats(self, store, our_p, enemy_p):
        for side, p in [("team", our_p), ("enemy", enemy_p)]:
            store[side]["k"].append(p["kills"])
            store[side]["d"].append(p["deaths"])
            store[side]["a"].append(p["assists"])
            store[side]["gold"].append(p["goldEarned"])
            store[side]["cs"].append(p["totalMinionsKilled"] + p["neutralMinionsKilled"])
            store[side]["dmg"].append(p["totalDamageDealtToChampions"])

    def _save_results(self, summary):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        file_path = os.path.join(self.base_results_dir, f"analysis_{timestamp}.txt")
        with open(file_path, "w") as f:
            f.write(summary)
        print(f"\nResults saved to: {file_path}")
        return file_path
