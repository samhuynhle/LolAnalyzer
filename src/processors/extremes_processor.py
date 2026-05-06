from src.processors.base import MetricProcessor

class ExtremesProcessor(MetricProcessor):
    def __init__(self):
        self.max_jungler_deficit = 0
        self.worst_jungler_match_id = None
        self.worst_jungler_champion = None
        self.worst_jungler_enemy_champion = None

    def analyze_match(self, match_data, target_puuid):
        if match_data["info"]["gameMode"] != "CLASSIC":
            return False

        p_list = match_data["info"]["participants"]
        me = next(p for p in p_list if p["puuid"] == target_puuid)
        team_id = me["teamId"]
        enemy_team_id = 200 if team_id == 100 else 100

        # If Spear Shot is the jungler, we don't track teammate jungler deficit
        if me["teamPosition"] == "JUNGLE":
            return False

        our_jungler = self._find_jungler(p_list, team_id)
        enemy_jungler = self._find_jungler(p_list, enemy_team_id)

        if our_jungler and enemy_jungler:
            deficit = enemy_jungler["goldEarned"] - our_jungler["goldEarned"]
            if deficit > self.max_jungler_deficit:
                self.max_jungler_deficit = deficit
                self.worst_jungler_match_id = match_data["metadata"]["matchId"]
                self.worst_jungler_champion = our_jungler["championName"]
                self.worst_jungler_enemy_champion = enemy_jungler["championName"]
                return True
        return False

    def get_results(self):
        return {
            "max_jungler_deficit": self.max_jungler_deficit,
            "worst_match_id": self.worst_jungler_match_id,
            "champion": self.worst_jungler_champion,
            "enemy_champion": self.worst_jungler_enemy_champion
        }

    def _find_jungler(self, participants, tid):
        j = next((p for p in participants if p["teamId"] == tid and p["teamPosition"] == "JUNGLE"), None)
        if j: return j
        return next((p for p in participants if p["teamId"] == tid and (p["summoner1Id"] == 11 or p["summoner2Id"] == 11)), None)
