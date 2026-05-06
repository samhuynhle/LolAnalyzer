from src.config import ROLES
from src.processors.base import MetricProcessor

class AveragesProcessor(MetricProcessor):
    def __init__(self):
        self.data_store = {}
        for prefix in ["PLAYER", "TEAMMATE"]:
            for role in ROLES:
                for outcome in ["WIN", "LOSS"]:
                    self.data_store[f"{prefix}_{role}_{outcome}"] = self._get_empty_stats()
        self.processed_count = 0

    def _get_empty_stats(self):
        return {"team": {"k":[],"d":[],"a":[],"gold":[],"cs":[],"dmg":[]}, 
                "enemy": {"k":[],"d":[],"a":[],"gold":[],"cs":[],"dmg":[]}}

    def analyze_match(self, match_data, target_puuid):
        if match_data["info"]["gameMode"] != "CLASSIC":
            return False
            
        p_list = match_data["info"]["participants"]
        me = next(p for p in p_list if p["puuid"] == target_puuid)
        team_id = me["teamId"]
        outcome = "WIN" if me["win"] else "LOSS"

        found_any_role = False
        for role in ROLES:
            our_p = self._find_participant(p_list, team_id, role)
            enemy_p = self._find_participant(p_list, team_id, role, find_enemy=True)

            if our_p and enemy_p:
                found_any_role = True
                prefix = "PLAYER" if our_p["puuid"] == target_puuid else "TEAMMATE"
                key = f"{prefix}_{role}_{outcome}"
                self._record_stats(self.data_store[key], our_p, enemy_p)
        
        if found_any_role:
            self.processed_count += 1
            return True
        return False

    def get_results(self):
        return {
            "data_store": self.data_store,
            "processed_count": self.processed_count
        }

    def _find_participant(self, p_list, team_id, role, find_enemy=False):
        target_team = team_id if not find_enemy else (200 if team_id == 100 else 100)
        p = next((p for p in p_list if p["teamId"] == target_team and p["teamPosition"] == role), None)
        if not p and role == "JUNGLE":
            # Fallback for Smite check (Summoner Spell ID 11)
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
