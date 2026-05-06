from abc import ABC, abstractmethod

class MetricProcessor(ABC):
    @abstractmethod
    def analyze_match(self, match_data, target_puuid):
        """
        Processes a single match's data for the target player.
        """
        pass

    @abstractmethod
    def get_results(self):
        """
        Returns the processed metrics in a structured format.
        """
        pass
