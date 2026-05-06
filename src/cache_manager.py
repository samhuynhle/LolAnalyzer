import os
import json
import hashlib

class CacheManager:
    def __init__(self, region, player_slug=None):
        if player_slug:
            self.cache_dir = os.path.join("cache", region.lower(), player_slug)
        else:
            self.cache_dir = os.path.join("cache", region.lower(), "global")
            
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_path(self, identifier):
        safe_name = hashlib.md5(identifier.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_name}.json")

    def get(self, identifier):
        path = self._get_path(identifier)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return None

    def save(self, identifier, data):
        path = self._get_path(identifier)
        with open(path, 'w') as f:
            json.dump(data, f)
