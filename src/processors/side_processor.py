from src.processors.base import MetricProcessor

class SideProcessor(MetricProcessor):
    def __init__(self):
        self.side_data = {
            "BLUE": self._get_empty_stats(), # Team 100
            "RED": self._get_empty_stats()   # Team 200
        }

    def _get_empty_stats(self):
        return {
            "games": 0,
            "wins": 0,
            "total_k": 0,
            "total_d": 0,
            "total_a": 0,
            "total_gold_diff": 0,
            "total_dmg_diff": 0
        }

    def analyze_match(self, match_data, target_puuid):
        if match_data["info"]["gameMode"] != "CLASSIC":
            return False

        p_list = match_data["info"]["participants"]
        me = next(p for p in p_list if p["puuid"] == target_puuid)
        
        # 100 is Blue, 200 is Red
        side = "BLUE" if me["teamId"] == 100 else "RED"
        
        # Find opponent in the same position
        role = me["teamPosition"]
        enemy_team_id = 200 if me["teamId"] == 100 else 100
        enemy_p = next((p for p in p_list if p["teamId"] == enemy_team_id and p["teamPosition"] == role), None)

        self.side_data[side]["games"] += 1
        if me["win"]:
            self.side_data[side]["wins"] += 1
            
        self.side_data[side]["total_k"] += me["kills"]
        self.side_data[side]["total_d"] += me["deaths"]
        self.side_data[side]["total_a"] += me["assists"]

        if enemy_p:
            self.side_data[side]["total_gold_diff"] += (me["goldEarned"] - enemy_p["goldEarned"])
            self.side_data[side]["total_dmg_diff"] += (me["totalDamageDealtToChampions"] - enemy_p["totalDamageDealtToChampions"])
            
        return True

    def get_results(self):
        results = {}
        for side, stats in self.side_data.items():
            if stats["games"] == 0:
                results[side] = None
                continue
            
            win_rate = stats["wins"] / stats["games"]
            avg_kda = (stats["total_k"] + stats["total_a"]) / max(stats["total_d"], 1)
            avg_gold_diff = stats["total_gold_diff"] / stats["games"]
            avg_dmg_diff = stats["total_dmg_diff"] / stats["games"]
            
            results[side] = {
                "games": stats["games"],
                "win_rate": win_rate,
                "kda": avg_kda,
                "gold_diff": avg_gold_diff,
                "dmg_diff": avg_dmg_diff
            }
        return results
