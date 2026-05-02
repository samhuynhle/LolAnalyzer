import os
import json
import time
import uuid

class DataManager:
    def __init__(self, registry_path="data/registry.json"):
        self.registry_path = registry_path
        self.data_dir = os.path.dirname(registry_path)
        self.matches_dir = os.path.join(self.data_dir, "matches")
        
        for d in [self.data_dir, self.matches_dir]:
            if not os.path.exists(d):
                os.makedirs(d)
        
        self.registry = self._load_registry()

    def _load_registry(self):
        if os.path.exists(self.registry_path):
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        return {"users": {}, "total_reports": 0}

    def _save_registry(self):
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=4)

    def _get_player_match_file(self, user_id):
        # Create a safe filename from the user_id (e.g. spear_shot#1111 -> spear_shot_1111.json)
        safe_name = user_id.replace("#", "_").replace(" ", "_")
        return os.path.join(self.matches_dir, f"{safe_name}.json")

    def _load_player_matches(self, user_id):
        path = self._get_player_match_file(user_id)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {}

    def _save_player_matches(self, user_id, matches):
        path = self._get_player_match_file(user_id)
        with open(path, 'w') as f:
            json.dump(matches, f, indent=4)

    def register_report(self, player_name, tag, region, file_path, match_count, processed_count, detailed_matches=None):
        user_id = f"{player_name}#{tag}".lower()
        
        if user_id not in self.registry["users"]:
            self.registry["users"][user_id] = {
                "name": player_name,
                "tag": tag,
                "region": region,
                "first_seen": time.strftime('%Y-%m-%d %H:%M:%S'),
                "last_analysis": "",
                "report_history": [],
                "match_history_file": f"matches/{user_id.replace('#', '_').replace(' ', '_')}.json"
            }
        
        user_entry = self.registry["users"][user_id]
        
        # Store detailed match data in its own specific file (table)
        if detailed_matches:
            matches = self._load_player_matches(user_id)
            for match in detailed_matches:
                mid = match["match_id"]
                matches[mid] = match
            
            # Sort matches by timestamp descending (newest first)
            sorted_matches = dict(sorted(
                matches.items(), 
                key=lambda item: item[1].get("timestamp", ""), 
                reverse=True
            ))
            
            self._save_player_matches(user_id, sorted_matches)

        # Update lightweight registry metadata
        report_entry = {
            "report_id": str(uuid.uuid4()),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "file_path": file_path,
            "match_count_requested": match_count,
            "matches_processed": processed_count
        }
        
        user_entry["report_history"].append(report_entry)
        
        # Sort report history by timestamp descending (newest first)
        user_entry["report_history"].sort(key=lambda x: x["timestamp"], reverse=True)
        
        user_entry["last_analysis"] = user_entry["report_history"][0]["timestamp"]
        self.registry["total_reports"] += 1
        
        self._save_registry()

    def get_user_history(self, player_name, tag):
        user_id = f"{player_name}#{tag}".lower()
        return self.registry["users"].get(user_id)

    def get_player_matches(self, player_name, tag):
        user_id = f"{player_name}#{tag}".lower()
        return self._load_player_matches(user_id)

    def list_all_users(self):
        return list(self.registry["users"].keys())
