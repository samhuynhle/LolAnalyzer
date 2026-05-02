import os
import shutil
from src.data_manager import DataManager

class DataResetter:
    def __init__(self, data_manager: DataManager):
        self.dm = data_manager
        self.root_dirs = ["cache", "results", "data"]

    def reset_all(self):
        """Wipes all generated data, cache, and the registry."""
        print("WARNING: This will delete ALL cached matches, generated reports, and the user registry.")
        confirm = input("Are you sure you want to proceed? (y/N): ")
        if confirm.lower() != 'y':
            print("Reset cancelled.")
            return

        for d in self.root_dirs:
            if os.path.exists(d):
                print(f"Cleaning {d}...")
                # We use a loop to avoid deleting the directory itself if we want to keep the structure,
                # but shutil.rmtree followed by makedirs is cleaner for a full reset.
                shutil.rmtree(d)
                os.makedirs(d)
        
        # Re-initialize the registry file
        self.dm.registry = {"users": {}, "total_reports": 0}
        self.dm._save_registry()
        print("Full reset complete.")

    def reset_player(self, player_name, tag):
        """Removes all data associated with a specific player."""
        user_id = f"{player_name}#{tag}".lower()
        user_history = self.dm.get_user_history(player_name, tag)
        
        if not user_history:
            print(f"No data found for player {player_name}#{tag}.")
            return

        print(f"Resetting all data for {player_name}#{tag}...")

        # 1. Remove partitioned files
        match_file = os.path.join("data", user_history["match_history_file"])
        report_file = os.path.join("data", user_history["report_history_file"])
        
        for f in [match_file, report_file]:
            if os.path.exists(f):
                os.remove(f)
                print(f"Deleted {f}")

        # 2. Remove player-specific result and cache folders
        region = user_history["region"]
        player_slug = f"{player_name.replace(' ', '_')}-{tag}"
        
        res_dir = os.path.join("results", region, player_slug)
        cache_dir = os.path.join("cache", region, player_slug)
        
        for d in [res_dir, cache_dir]:
            if os.path.exists(d):
                shutil.rmtree(d)
                print(f"Deleted directory {d}")

        # 3. Remove from registry
        del self.dm.registry["users"][user_id]
        self.dm._save_registry()
        
        print(f"Reset for {player_name}#{tag} complete.")
