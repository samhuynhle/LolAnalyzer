import os
import json
import time
import uuid

class DataManager:
    def __init__(self, registry_path="data/registry.json"):
        self.registry_path = registry_path
        self.data_dir = os.path.dirname(registry_path)
        self.matches_dir = os.path.join(self.data_dir, "matches")
        self.reports_dir = os.path.join(self.data_dir, "reports")
        
        for d in [self.data_dir, self.matches_dir, self.reports_dir]:
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

    def _get_player_file_path(self, user_id, folder):
        safe_name = user_id.replace("#", "_").replace(" ", "_")
        return os.path.join(folder, f"{safe_name}.json")

    def _load_json_file(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {}

    def _save_json_file(self, path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def register_report(self, player_name, tag, region, file_path, match_count, processed_count, detailed_matches=None):
        user_id = f"{player_name}#{tag}".lower()
        safe_id = user_id.replace("#", "_").replace(" ", "_")
        
        if user_id not in self.registry["users"]:
            self.registry["users"][user_id] = {
                "name": player_name,
                "tag": tag,
                "region": region,
                "first_seen": time.strftime('%Y-%m-%d %H:%M:%S'),
                "last_analysis": "",
                "match_history_file": f"matches/{safe_id}.json",
                "report_history_file": f"reports/{safe_id}.json"
            }
        
        user_entry = self.registry["users"][user_id]
        
        # 1. Update Match History Table
        if detailed_matches:
            match_file = self._get_player_file_path(user_id, self.matches_dir)
            matches = self._load_json_file(match_file)
            for m in detailed_matches:
                matches[m["match_id"]] = m
            
            # Sort matches by timestamp descending
            sorted_matches = dict(sorted(
                matches.items(), 
                key=lambda x: x[1].get("timestamp", ""), 
                reverse=True
            ))
            self._save_json_file(match_file, sorted_matches)

        # 2. Update Report History Table
        report_file = self._get_player_file_path(user_id, self.reports_dir)
        reports = self._load_json_file(report_file)
        
        report_id = str(uuid.uuid4())
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        reports[report_id] = {
            "report_id": report_id,
            "timestamp": timestamp,
            "file_path": file_path,
            "match_count_requested": match_count,
            "matches_processed": processed_count
        }
        
        # Sort reports by timestamp descending
        sorted_reports = dict(sorted(
            reports.items(),
            key=lambda x: x[1].get("timestamp", ""),
            reverse=True
        ))
        self._save_json_file(report_file, sorted_reports)

        # 3. Update Registry Metadata
        user_entry["last_analysis"] = timestamp
        self.registry["total_reports"] += 1
        self._save_registry()

    def get_user_history(self, player_name, tag):
        user_id = f"{player_name}#{tag}".lower()
        return self.registry["users"].get(user_id)

    def get_player_matches(self, player_name, tag):
        user_id = f"{player_name}#{tag}".lower()
        match_file = self._get_player_file_path(user_id, self.matches_dir)
        return self._load_json_file(match_file)

    def get_player_reports(self, player_name, tag):
        user_id = f"{player_name}#{tag}".lower()
        report_file = self._get_player_file_path(user_id, self.reports_dir)
        return self._load_json_file(report_file)

    def list_all_users(self):
        return list(self.registry["users"].keys())
