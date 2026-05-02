import time
from src.config import ROLES, ROLE_MAP

class ReportGenerator:
    def __init__(self, player_name, tag, region):
        self.player_name = player_name
        self.tag = tag
        self.region = region

    def generate(self, match_ids, data_store, processed_count):
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
        if "PLAYER" in label:
            who = self.player_name
            if "OVERALL" in label: condition = f"{self.player_name} played any role"
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
            if "ALL ROLES" in label:
                who = f"{self.player_name}'s teammates"
                condition = f"{self.player_name}'s teammates played any role"
            else:
                role_key = next((r for r in ROLES if r in label or (r=="UTILITY" and "SUPPORT" in label)), "role")
                specific_role = ROLE_MAP.get(role_key, "teammate")
                who = f"{self.player_name}'s {specific_role}"
                if "WINS" in label: condition = f"{who} won"
                elif "LOSSES" in label: condition = f"{who} lost"
                else: condition = f"{who} played"

        lead_trail = "a lead of" if g_diff >= 0 else "a deficit of"
        d_lead_trail = "a lead of" if d_diff >= 0 else "a deficit of"
        res += f"\nIn the {display_c} games where {condition}, {who} averaged {lead_trail} {abs(g_diff):,.0f} gold and {d_lead_trail} {abs(d_diff):,.0f} damage per game.\n"
        res += f"{'='*65}\n"
        return res
