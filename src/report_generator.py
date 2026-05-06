import time
from src.config import ROLES, ROLE_MAP

class ReportGenerator:
    def __init__(self, player_name, tag, region):
        self.player_name = player_name
        self.tag = tag
        self.region = region

    def generate(self, match_ids, pipeline_results):
        avg_results = pipeline_results["averages"]
        data_store = avg_results["data_store"]
        processed_count = avg_results["processed_count"]

        output =  "============================================================\n"
        output += "           LOL PERFORMANCE ANALYSIS (AVERAGES)\n"
        output += "============================================================\n"
        output += f"Target Player:  {self.player_name}#{self.tag}\n"
        output += f"Region:         {self.region.upper()}\n"
        output += f"Total Matches:  {processed_count} (out of {len(match_ids)} fetched)\n"
        output += f"Generated On:   {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += "Note: All values below represent averages per game.\n"
        output += "============================================================\n"

        for role in ROLES:
            role_label = role.replace("UTILITY", "SUPPORT")
            output += f"\n\n{'#'*65}\n"
            output += f"                {role_label} ROLE ANALYSIS\n"
            output += f"{'#'*65}\n"
            output += self._format_section(f"PLAYER {role_label} - WINS", data_store[f"PLAYER_{role}_WIN"], processed_count)
            output += self._format_section(f"PLAYER {role_label} - LOSSES", data_store[f"PLAYER_{role}_LOSS"], processed_count)
            output += self._format_section(f"TEAMMATE {role_label} - WINS", data_store[f"TEAMMATE_{role}_WIN"], processed_count)
            output += self._format_section(f"TEAMMATE {role_label} - LOSSES", data_store[f"TEAMMATE_{role}_LOSS"], processed_count)
            output += self._format_section(f"ALL PLAYER {role_label} GAMES", self._combine(data_store, [f"PLAYER_{role}_WIN", f"PLAYER_{role}_LOSS"]), processed_count)
            output += self._format_section(f"ALL TEAMMATE {role_label} GAMES", self._combine(data_store, [f"TEAMMATE_{role}_WIN", f"TEAMMATE_{role}_LOSS"]), processed_count)

        output += "\n\n" + "="*60 + "\n"
        output += "                SUMMARY AGGREGATES (ALL ROLES)\n"
        output += "="*60 + "\n"
        
        all_p_keys = [f"PLAYER_{r}_{o}" for r in ROLES for o in ["WIN", "LOSS"]]
        all_t_keys = [f"TEAMMATE_{r}_{o}" for r in ROLES for o in ["WIN", "LOSS"]]
        
        output += self._format_section(f"OVERALL {self.player_name.upper()} PERFORMANCE (ALL ROLES)", self._combine(data_store, all_p_keys), processed_count)
        output += self._format_section(f"OVERALL TEAMMATE PERFORMANCE (ALL ROLES)", self._combine(data_store, all_t_keys), processed_count)
        output += self._format_section("GRAND OVERALL PERFORMANCE (EVERYONE)", self._combine(data_store, all_p_keys + all_t_keys), processed_count)

        # Extreme Metrics Section
        if "extremes" in pipeline_results:
            ext = pipeline_results["extremes"]
            output += "\n\n" + "="*60 + "\n"
            output += "                EXTREME PERFORMANCE METRICS\n"
            output += "="*60 + "\n"
            if ext["max_jungler_deficit"] > 0:
                output += f"\n>>> LARGEST TEAMMATE JUNGLER DEFICIT\n"
                output += f"{'-'*60}\n"
                output += f"Max Gold Deficit:  {ext['max_jungler_deficit']:,} gold\n"
                output += f"Teammate Champ:    {ext['champion']}\n"
                output += f"Enemy Champ:       {ext['enemy_champion']}\n"
                output += f"Match ID:          {ext['worst_match_id']}\n"
                output += f"\nIn the worst-case scenario, {self.player_name}'s jungler ({ext['champion']}) was out-farmed/out-played by {ext['max_jungler_deficit']:,} gold compared to the enemy {ext['enemy_champion']}.\n"
            else:
                output += "\nNo significant extremes recorded in this batch.\n"
            output += "="*60 + "\n"

        # Win Condition Correlation Section
        if "correlation" in pipeline_results and pipeline_results["correlation"]:
            corr_data = pipeline_results["correlation"]
            output += "\n\n" + "="*60 + "\n"
            output += "                WIN CONDITION CORRELATION\n"
            output += "="*60 + "\n"
            
            output += "Pearson Correlation Coefficients (Relationship to Winning):\n"
            output += f"{'-'*60}\n"
            for metric, val in corr_data["correlations"].items():
                label = metric.replace("_", " ").title().replace("Dmg", "Damage").replace("Cs", "CS")
                output += f"{label:<25} {val:>+6.2f}\n"
            
            best_metric = corr_data["best_metric"]
            best_label = best_metric.replace("_", " ").title().replace("Dmg", "Damage").replace("Cs", "CS")
            output += f"\n>>> MOST IMPACTFUL METRIC: {best_label}\n"
            output += f"{'-'*60}\n"
            output += f"{'PERFORMANCE TIER':<25} {'VALUE RANGE':<25} {'WIN RATE'}\n"
            
            for q in corr_data["quartiles"]:
                tier_label = {1: "Bottom 25%", 2: "Below Average", 3: "Above Average", 4: "Top 25%"}[q["tier"]]
                range_str = f"{q['min']:.0f} to {q['max']:.0f}"
                if best_metric == "kda":
                    range_str = f"{q['min']:.1f} to {q['max']:.1f}"
                output += f"{tier_label:<25} {range_str:<25} {q['win_rate']*100:>6.1f}%\n"

            output += f"\nConclusion: {self.player_name}'s success is most closely tied to their {best_label}.\n"
            output += "="*60 + "\n"

        # Role Impact Recommendation Section
        if "role_impact" in pipeline_results and pipeline_results["role_impact"]:
            rankings = pipeline_results["role_impact"]
            output += "\n\n" + "="*60 + "\n"
            output += "                ROLE IMPACT RECOMMENDATION (COMPOUNDED)\n"
            output += "="*60 + "\n"
            
            is_weighted = rankings[0].get("weighted", False)
            if is_weighted:
                output += "NOTE: Scores are weighted by personal Win Condition Correlates\n"
                output += "      and include Teammate Liability (Loss Rate without you).\n"
                output += f"{'-'*60}\n"

            output += f"{'ROLE':<12} {'GMS':<5} {'WIN%':<7} {'KDA':<6} {'LIABILITY':<11} {'COMP. SCORE'}\n"
            output += f"{'-'*60}\n"
            
            for i, r in enumerate(rankings):
                tag = "[OPTIMAL]" if i == 0 else ""
                output += f"{r['role']:<12} {r['games']:<5} {r['win_rate']*100:<7.1f} {r['avg_kda']:<6.1f} {r['liability_score']:<11.1f} {r['score']:<10.1f} {tag}\n"
            
            best = rankings[0]
            output += f"\nBased on {processed_count} games, {self.player_name} should prioritize playing {best['role']}.\n"
            output += f"In this role, they maintain a {best['win_rate']*100:.1f}% win rate, a {best['avg_kda']:.1f} KDA, and average\n"
            output += f"a {best['avg_gold_diff']:+,.0f} gold lead and a {best['avg_dmg_diff']:+,.0f} damage lead.\n"
            output += f"\nCompounded Result: The team loses {best['liability_score']:.1f}% of games when you are NOT in this role.\n"
            output += "="*60 + "\n"

        # Side Bias Section
        if "side_bias" in pipeline_results:
            side_data = pipeline_results["side_bias"]
            output += "\n\n" + "="*60 + "\n"
            output += "                MAP SIDE PERFORMANCE BIAS\n"
            output += "="*60 + "\n"
            output += f"{'SIDE':<10} {'GAMES':<8} {'WIN%':<10} {'KDA':<10} {'GOLD DIFF':<15}\n"
            output += f"{'-'*60}\n"
            
            for side in ["BLUE", "RED"]:
                s = side_data.get(side)
                if not s: continue
                output += f"{side:<10} {s['games']:<8} {s['win_rate']*100:<10.1f} {s['kda']:<10.1f} {s['gold_diff']:<+15.0f}\n"
            
            blue = side_data.get("BLUE")
            red = side_data.get("RED")
            if blue and red:
                diff = (blue["win_rate"] - red["win_rate"]) * 100
                favored = "Blue" if diff > 0 else "Red"
                if abs(diff) > 5:
                    output += f"\nConclusion: {self.player_name} is significantly favored on {favored} Side ({max(blue['win_rate'], red['win_rate'])*100:.1f}% {favored} vs {min(blue['win_rate'], red['win_rate'])*100:.1f}% {'Red' if favored=='Blue' else 'Blue'}).\n"
                else:
                    output += f"\nConclusion: {self.player_name} maintains consistent performance across both sides ({blue['win_rate']*100:.1f}% Blue / {red['win_rate']*100:.1f}% Red).\n"
            output += "="*60 + "\n"

        # Carry Weight Section
        if "carry_weight" in pipeline_results:
            cw_data = pipeline_results["carry_weight"]
            output += "\n\n" + "="*60 + "\n"
            output += "                CARRY WEIGHT & COMPENSATION ANALYSIS\n"
            output += "="*60 + "\n"
            output += "Performance when your teammates are underperforming (Losing Lane):\n\n"

            # Sort my roles by most played
            sorted_my_roles = sorted(cw_data.keys(), 
                                     key=lambda r: sum(t['deficit_games'] for t in cw_data[r].values()), 
                                     reverse=True)

            for my_role in sorted_my_roles[:2]:
                my_role_label = my_role.replace("UTILITY", "SUPPORT")
                output += f">>> WHEN PLAYING {my_role_label}:\n"
                output += f"{'TEAMMATE':<12} {'FAIL%':<8} {'CARRY WR%':<11} {'REQ. GOLD':<12} {'DEPENDENCY'}\n"
                output += f"{'-'*65}\n"
                
                teammates = cw_data[my_role]
                # Sort by fail% to see biggest liabilities
                sorted_teammates = sorted(teammates.keys(), key=lambda t: teammates[t]['fail_rate'], reverse=True)
                
                for t_role in sorted_teammates:
                    t = teammates[t_role]
                    t_label = t_role.replace("UTILITY", "SUPPORT")
                    
                    dep_val = t['dependency']
                    dep_str = "None"
                    if dep_val > 0.6: dep_str = "Critical"
                    elif dep_val > 0.4: dep_str = "Strong"
                    elif dep_val > 0.2: dep_str = "Moderate"
                    elif dep_val > 0: dep_str = "Low"
                    
                    output += f"{t_label:<12} {t['fail_rate']*100:<8.1f} {t['carry_win_rate']*100:<11.1f} {t['req_carry_gold']:<12.0f} {dep_str}\n"
                
                # Logic to find the lane that requires most compensation
                worst_lane = sorted_teammates[0]
                output += f"\nConclusion: When playing {my_role_label}, your {worst_lane.replace('UTILITY', 'SUPPORT')} is the most frequent liability.\n"
                output += f"Carrying their failure requires an average lead of {teammates[worst_lane]['req_carry_gold']:+,.0f} gold from you.\n"
                output += f"{'-'*65}\n\n"

            output += "="*60 + "\n"

        return output

    def _combine(self, data_store, keys):
        comb = {"team": {"k":[],"d":[],"a":[],"gold":[],"cs":[],"dmg":[]}, 
                "enemy": {"k":[],"d":[],"a":[],"gold":[],"cs":[],"dmg":[]}}
        for k in keys:
            if k not in data_store: continue
            for side in ["team", "enemy"]:
                for metric in comb[side]:
                    comb[side][metric].extend(data_store[k][side][metric])
        return comb

    def _format_section(self, label, data, processed_count):
        c = len(data["team"]["k"])
        if c == 0: return ""
        display_c = processed_count if ("ALL ROLES" in label or "EVERYONE" in label) else c

        def avg(key, side="team"): return sum(data[side][key]) / c
        tk, td, ta = avg("k"), avg("d"), avg("a")
        ek, ed, ea = avg("k", "enemy"), avg("d", "enemy"), avg("a", "enemy")
        g_diff, d_diff = avg("gold") - avg("gold", "enemy"), avg("dmg") - avg("dmg", "enemy")
        
        res = f"\n>>> {label} ({display_c} Games)\n"
        res += f"{'METRIC':<15} {'AVG TEAM':<15} {'AVG ENEMY':<15} {'AVG DIFF':<15}\n"
        res += f"{'-'*65}\n"
        tkda, ekda, dkda = f"{tk:.1f}/{td:.1f}/{ta:.1f}", f"{ek:.1f}/{ed:.1f}/{ea:.1f}", f"{tk-ek:+.1f}/{td-ed:+.1f}/{ta-ea:+.1f}"
        res += f"{'K/D/A':<15} {tkda:<15} {ekda:<15} {dkda:<15}\n"
        res += f"{'Gold':<15} {avg('gold'):<15.0f} {avg('gold', 'enemy'):<15.0f} {g_diff:<+15.0f}\n"
        res += f"{'CS':<15} {avg('cs'):<15.1f} {avg('cs', 'enemy'):<15.1f} {avg('cs')-avg('cs','enemy'):<+15.1f}\n"
        res += f"{'Damage':<15} {avg('dmg'):<15.0f} {avg('dmg', 'enemy'):<15.0f} {d_diff:<+15.0f}\n"
        
        # Narrative logic
        if "PLAYER" in label or self.player_name.upper() in label:
            who = self.player_name
            if "OVERALL" in label: 
                condition = f"{self.player_name} played any role"
            else:
                role_key = next((r for r in ROLES if r in label or (r=="UTILITY" and "SUPPORT" in label)), "role")
                role_desc = "mid" if role_key == "MIDDLE" else role_key.lower() if role_key != "UTILITY" else "support"
                if "WINS" in label: condition = f"{self.player_name} won playing {role_desc}"
                elif "LOSSES" in label: condition = f"{self.player_name} lost playing {role_desc}"
                else: condition = f"{self.player_name} played {role_desc}"
        elif "EVERYONE" in label:
            who = "The collective players"
            condition = "all roles were combined"
        else:
            role_key = next((r for r in ROLES if r in label or (r=="UTILITY" and "SUPPORT" in label)), "role")
            role_desc = "mid" if role_key == "MIDDLE" else role_key.lower() if role_key != "UTILITY" else "support"
            if "ALL ROLES" in label:
                who = f"{self.player_name}'s teammates"
                condition = f"{self.player_name}'s teammates played any role"
            else:
                specific_role = ROLE_MAP.get(role_key, "teammate")
                who = f"their {specific_role}"
                if "WINS" in label: condition = f"{who} won"
                elif "LOSSES" in label: condition = f"{who} lost"
                else: condition = f"{self.player_name} didn't play {role_desc}"

        lead_trail = "a lead of" if g_diff >= 0 else "a deficit of"
        d_lead_trail = "a lead of" if d_diff >= 0 else "a deficit of"
        res += f"\nIn the {display_c} games where {condition}, {who} averaged {lead_trail} {abs(g_diff):,.0f} gold and they averaged {d_lead_trail} {abs(d_diff):,.0f} damage per game.\n"
        res += f"{'='*65}\n"
        return res
