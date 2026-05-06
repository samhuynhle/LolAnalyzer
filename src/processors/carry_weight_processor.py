import math
from src.processors.base import MetricProcessor
from src.config import ROLES

class CarryWeightProcessor(MetricProcessor):
    def __init__(self):
        # data[my_role][t_role]
        self.data = {}
        # We also need total games in each role to calculate fail rate
        self.total_role_games = {role: 0 for role in ROLES}
        
        for my_role in ROLES:
            self.data[my_role] = {}
            for t_role in ROLES:
                if my_role == t_role: continue
                self.data[my_role][t_role] = {
                    "deficit_games": 0,
                    "deficit_wins": 0,
                    "wins_my_gold_diffs": [],
                    "all_my_gold_diffs": [],
                    "all_win_outcomes": []
                }

    def analyze_match(self, match_data, target_puuid):
        if match_data["info"]["gameMode"] != "CLASSIC":
            return False

        p_list = match_data["info"]["participants"]
        me = next(p for p in p_list if p["puuid"] == target_puuid)
        my_role = me["teamPosition"]
        
        if not my_role or my_role not in self.data:
            return False

        self.total_role_games[my_role] += 1
        team_id = me["teamId"]
        enemy_team_id = 200 if team_id == 100 else 100
        is_win = me["win"]
        my_gold_earned = me["goldEarned"]

        for t_role in ROLES:
            if t_role == my_role: continue
            
            teammate = next((p for p in p_list if p["teamId"] == team_id and p["teamPosition"] == t_role), None)
            opponent = next((p for p in p_list if p["teamId"] == enemy_team_id and p["teamPosition"] == t_role), None)
            
            if teammate and opponent:
                t_gold_diff = teammate["goldEarned"] - opponent["goldEarned"]
                
                # We only care about games where the teammate underperformed (Negative Gold Diff)
                if t_gold_diff < 0:
                    my_gold_diff = my_gold_earned - next(p for p in p_list if p["teamId"] == enemy_team_id and p["teamPosition"] == my_role)["goldEarned"]
                    
                    bucket = self.data[my_role][t_role]
                    bucket["deficit_games"] += 1
                    if is_win:
                        bucket["deficit_wins"] += 1
                        bucket["wins_my_gold_diffs"].append(my_gold_diff)
                    
                    bucket["all_my_gold_diffs"].append(my_gold_diff)
                    bucket["all_win_outcomes"].append(1 if is_win else 0)
                
        return True

    def get_results(self):
        results = {}
        for my_role, teammates in self.data.items():
            if self.total_role_games[my_role] == 0: continue
            
            results[my_role] = {}
            for t_role, stats in teammates.items():
                if stats["deficit_games"] == 0: continue
                
                fail_rate = stats["deficit_games"] / self.total_role_games[my_role]
                carry_win_rate = stats["deficit_wins"] / stats["deficit_games"]
                req_carry_gold = sum(stats["wins_my_gold_diffs"]) / len(stats["wins_my_gold_diffs"]) if stats["wins_my_gold_diffs"] else 0
                
                # Dependency: Correlation between my gold lead and win specifically when this teammate is losing
                dependency = self._pearson_correlation(stats["all_my_gold_diffs"], stats["all_win_outcomes"])
                
                results[my_role][t_role] = {
                    "deficit_games": stats["deficit_games"],
                    "fail_rate": fail_rate,
                    "carry_win_rate": carry_win_rate,
                    "req_carry_gold": req_carry_gold,
                    "dependency": dependency
                }
        return results

    def _pearson_correlation(self, x, y):
        n = len(x)
        if n < 3: return 0 # Need more data for meaningful correlation
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_x2 = sum(i**2 for i in x)
        sum_y2 = sum(i**2 for i in y)
        sum_xy = sum(i*j for i, j in zip(x, y))

        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2))

        if denominator == 0:
            return 0
        return numerator / denominator
