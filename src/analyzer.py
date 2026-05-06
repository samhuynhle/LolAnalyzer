import os
import time
from src.config import RANKED_QUEUES
from src.fetcher import MatchFetcher
from src.processors.averages_processor import AveragesProcessor
from src.processors.extremes_processor import ExtremesProcessor
from src.processors.role_impact_processor import RoleImpactProcessor
from src.processors.correlation_processor import CorrelationProcessor
from src.processors.side_processor import SideProcessor
from src.processors.carry_weight_processor import CarryWeightProcessor
from src.report_generator import ReportGenerator
from src.data_manager import DataManager

class MatchAnalyzer:
    def __init__(self, api_key, name, tag, region=None, match_count=52):
        self.name = name.strip()
        self.tag = tag.strip()
        self.match_count = match_count
        
        self.validate_inputs()
        
        self.fetcher = MatchFetcher(api_key, region)
        self.data_manager = DataManager()
        
        # Initialize processors
        self.processors = {
            "averages": AveragesProcessor(),
            "extremes": ExtremesProcessor(),
            "role_impact": RoleImpactProcessor(),
            "correlation": CorrelationProcessor(),
            "side_bias": SideProcessor(),
            "carry_weight": CarryWeightProcessor()
        }
        
        self.region = None
        self.player_slug = None
        self.puuid = None
        self.base_results_dir = None
        self.report_gen = None

    def validate_inputs(self):
        if len(self.name) < 3 or len(self.name) > 16:
            raise ValueError(f"Invalid Riot Name: '{self.name}'. Must be between 3 and 16 characters.")
        if len(self.tag) < 3 or len(self.tag) > 5:
            raise ValueError(f"Invalid Riot Tag: '{self.tag}'. Must be between 3 and 5 characters.")

    def run(self, queue=None):
        # 1. Player & Region Discovery
        self.region, self.puuid, self.player_slug = self.fetcher.discover_player(self.name, self.tag)
        if not self.region:
            print(f"Could not find player {self.name}#{self.tag} in any region.")
            return

        self.base_results_dir = os.path.join("results", self.region, self.player_slug)
        if not os.path.exists(self.base_results_dir):
            os.makedirs(self.base_results_dir)
            
        self.report_gen = ReportGenerator(self.name, self.tag, self.region)

        # 2. Fetch Match IDs
        match_ids = self.fetcher.fetch_match_ids(self.puuid, self.match_count, queue)
        if not match_ids:
            print(f"No matches found for {self.name}#{self.tag}.")
            return

        # 3. Processing Loop
        print(f"Analyzing {len(match_ids)} matches for {self.name}#{self.tag} ({self.region})...")
        detailed_results = []
        
        for mid in match_ids:
            try:
                time.sleep(0.05)
                m = self.fetcher.fetch_match_details(mid)
                
                # Ranked Validation
                if m["info"]["gameMode"] != "CLASSIC":
                    continue
                if m["info"]["queueId"] not in RANKED_QUEUES:
                    continue
                
                # Run all processors
                for p_name, processor in self.processors.items():
                    processor.analyze_match(m, self.puuid)
                
                # Capture detailed result for the target player (for DataManager)
                p_list = m["info"]["participants"]
                me = next(p for p in p_list if p["puuid"] == self.puuid)
                detailed_results.append({
                    "match_id": mid,
                    "champion": me["championName"],
                    "role": me["teamPosition"],
                    "win": me["win"],
                    "kills": me["kills"],
                    "deaths": me["deaths"],
                    "assists": me["assists"],
                    "gold": me["goldEarned"],
                    "damage": me["totalDamageDealtToChampions"],
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(m["info"]["gameCreation"]/1000.0))
                })

            except Exception as e:
                print(f"Error analyzing match {mid}: {e}")

        # 4. Gather Results & Report
        # Gather correlation first to weight the role impact
        corr_results = self.processors["correlation"].get_results()
        
        pipeline_results = {
            "averages": self.processors["averages"].get_results(),
            "extremes": self.processors["extremes"].get_results(),
            "correlation": corr_results,
            "role_impact": self.processors["role_impact"].get_results(correlation_weights=corr_results.get("correlations")),
            "side_bias": self.processors["side_bias"].get_results(),
            "carry_weight": self.processors["carry_weight"].get_results()
        }
        
        processed_count = pipeline_results["averages"]["processed_count"]
        
        if processed_count == 0:
            print(f"\nNo valid CLASSIC matches found for {self.name}#{self.tag}.")
            return

        summary = self.report_gen.generate(match_ids, pipeline_results)
        saved_path = self._save_results(summary)
        
        # 5. Persistence
        self.data_manager.register_report(
            self.name, self.tag, self.region, 
            saved_path, self.match_count, processed_count,
            detailed_matches=detailed_results
        )
        
        return {
            "player": f"{self.name}#{self.tag}",
            "region": self.region,
            "match_count_requested": self.match_count,
            "matches_processed": processed_count,
            "report_path": saved_path,
            "summary": summary,
            "pipeline_results": pipeline_results
        }

    def _save_results(self, summary):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        file_path = os.path.join(self.base_results_dir, f"analysis_{timestamp}.txt")
        with open(file_path, "w") as f:
            f.write(summary)
        print(f"\nResults saved to: {file_path}")
        return file_path
