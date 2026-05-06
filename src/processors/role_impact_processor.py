from src.processors.base import MetricProcessor
from src.config import ROLES

class RoleImpactProcessor(MetricProcessor):
    def __init__(self, min_games=3):
        self.min_games = min_games
        self.role_data = {}
        for role in ROLES:
            self.role_data[role] = {
                "games": 0,
                "wins": 0,
                "total_gold_diff": 0,
                "total_dmg_diff": 0,
                "total_cs_diff": 0,
                "total_kills": 0,
                "total_deaths": 0,
                "total_assists": 0,
                "games_not_played": 0,
                "wins_not_played": 0
            }

    def analyze_match(self, match_data, target_puuid):
        if match_data["info"]["gameMode"] != "CLASSIC":
            return False

        p_list = match_data["info"]["participants"]
        me = next(p for p in p_list if p["puuid"] == target_puuid)
        role_played = me["teamPosition"]
        
        if not role_played or role_played not in self.role_data:
            return False

        # 1. Update stats for the role actually played
        team_id = me["teamId"]
        enemy_team_id = 200 if team_id == 100 else 100
        enemy_p = next((p for p in p_list if p["teamId"] == enemy_team_id and p["teamPosition"] == role_played), None)
        
        self.role_data[role_played]["games"] += 1
        if me["win"]:
            self.role_data[role_played]["wins"] += 1
        
        self.role_data[role_played]["total_kills"] += me["kills"]
        self.role_data[role_played]["total_deaths"] += me["deaths"]
        self.role_data[role_played]["total_assists"] += me["assists"]

        if enemy_p:
            self.role_data[role_played]["total_gold_diff"] += (me["goldEarned"] - enemy_p["goldEarned"])
            self.role_data[role_played]["total_dmg_diff"] += (me["totalDamageDealtToChampions"] - enemy_p["totalDamageDealtToChampions"])
            self.role_data[role_played]["total_cs_diff"] += (me["totalMinionsKilled"] + me["neutralMinionsKilled"]) - \
                                                             (enemy_p["totalMinionsKilled"] + enemy_p["neutralMinionsKilled"])
        
        # 2. Update stats for roles NOT played (Teammate Liability)
        for role in ROLES:
            if role != role_played:
                self.role_data[role]["games_not_played"] += 1
                if me["win"]:
                    self.role_data[role]["wins_not_played"] += 1
            
        return True

    def get_results(self, correlation_weights=None):
        rankings = []
        for role, stats in self.role_data.items():
            if stats["games"] < self.min_games:
                continue
            
            win_rate = stats["wins"] / stats["games"]
            avg_gold_diff = stats["total_gold_diff"] / stats["games"]
            avg_dmg_diff = stats["total_dmg_diff"] / stats["games"]
            avg_cs_diff = stats["total_cs_diff"] / stats["games"]
            avg_kda = (stats["total_kills"] + stats["total_assists"]) / max(stats["total_deaths"], 1)
            
            # Team performance when NOT playing this role
            not_played_wr = stats["wins_not_played"] / max(stats["games_not_played"], 1)
            liability_score = (1.0 - not_played_wr) * 100  # Percentage loss rate when absent
            
            if correlation_weights:
                # Personalized scoring
                score = (win_rate * 100)
                w = correlation_weights
                if w.get("gold_diff", 0) > 0:
                    score += (avg_gold_diff / 100) * w["gold_diff"]
                if w.get("dmg_diff", 0) > 0:
                    score += (avg_dmg_diff / 1000) * w["dmg_diff"]
                if w.get("cs_diff", 0) > 0:
                    score += avg_cs_diff * w["cs_diff"]
                if w.get("kda", 0) > 0:
                    score += (avg_kda * 10) * w["kda"]
            else:
                score = (win_rate * 100) + (avg_gold_diff / 100) + (avg_dmg_diff / 1000)
            
            # Compounded Score = Personal Impact + Teammate Liability
            compounded_score = score + liability_score
            
            rankings.append({
                "role": role.replace("UTILITY", "SUPPORT"),
                "games": stats["games"],
                "win_rate": win_rate,
                "avg_gold_diff": avg_gold_diff,
                "avg_dmg_diff": avg_dmg_diff,
                "avg_kda": avg_kda,
                "liability_score": liability_score,
                "score": compounded_score,
                "weighted": bool(correlation_weights)
            })
        
        # Sort by compounded score descending
        rankings.sort(key=lambda x: x["score"], reverse=True)
        return rankings
