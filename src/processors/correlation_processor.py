import math
from src.processors.base import MetricProcessor

class CorrelationProcessor(MetricProcessor):
    def __init__(self):
        self.matches = []

    def analyze_match(self, match_data, target_puuid):
        if match_data["info"]["gameMode"] != "CLASSIC":
            return False

        p_list = match_data["info"]["participants"]
        me = next(p for p in p_list if p["puuid"] == target_puuid)
        role = me["teamPosition"]
        
        if not role:
            return False

        team_id = me["teamId"]
        enemy_team_id = 200 if team_id == 100 else 100
        enemy_p = next((p for p in p_list if p["teamId"] == enemy_team_id and p["teamPosition"] == role), None)

        if not enemy_p:
            return False

        # Metrics for this specific match
        win = 1 if me["win"] else 0
        gold_diff = me["goldEarned"] - enemy_p["goldEarned"]
        dmg_diff = me["totalDamageDealtToChampions"] - enemy_p["totalDamageDealtToChampions"]
        cs_diff = (me["totalMinionsKilled"] + me["neutralMinionsKilled"]) - \
                  (enemy_p["totalMinionsKilled"] + enemy_p["neutralMinionsKilled"])
        kda = (me["kills"] + me["assists"]) / max(me["deaths"], 1)

        self.matches.append({
            "win": win,
            "gold_diff": gold_diff,
            "dmg_diff": dmg_diff,
            "cs_diff": cs_diff,
            "kda": kda
        })
        return True

    def get_results(self):
        if len(self.matches) < 5:
            return {}

        metrics = ["gold_diff", "dmg_diff", "cs_diff", "kda"]
        correlations = {}
        wins = [m["win"] for m in self.matches]

        for metric in metrics:
            values = [m[metric] for m in self.matches]
            correlations[metric] = self._pearson_correlation(values, wins)

        # Find best metric
        best_metric = max(correlations, key=lambda k: abs(correlations[k]))
        
        # Calculate Quartiles for best metric
        quartiles = self._calculate_quartiles(best_metric)

        return {
            "correlations": correlations,
            "best_metric": best_metric,
            "quartiles": quartiles
        }

    def _pearson_correlation(self, x, y):
        n = len(x)
        if n == 0: return 0
        
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

    def _calculate_quartiles(self, metric):
        sorted_matches = sorted(self.matches, key=lambda x: x[metric])
        n = len(sorted_matches)
        if n < 4: return []

        q_size = n // 4
        quartiles_data = []

        for i in range(4):
            start = i * q_size
            end = (i + 1) * q_size if i < 3 else n
            group = sorted_matches[start:end]
            
            avg_win_rate = sum(m["win"] for m in group) / len(group)
            min_val = group[0][metric]
            max_val = group[-1][metric]
            
            quartiles_data.append({
                "tier": i + 1,
                "min": min_val,
                "max": max_val,
                "win_rate": avg_win_rate,
                "count": len(group)
            })

        return quartiles_data
