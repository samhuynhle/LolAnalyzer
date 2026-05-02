from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
import time

@dataclass
class MatchRecord:
    match_id: str
    champion: str
    role: str
    win: bool
    kills: int
    deaths: int
    assists: int
    gold: int
    damage: int
    timestamp: str

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class ReportEntry:
    report_id: str
    timestamp: str
    file_path: str
    match_count_requested: int
    matches_processed: int

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class UserMetadata:
    name: str
    tag: str
    region: str
    first_seen: str
    last_analysis: str
    match_history_file: str
    report_history_file: str

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class RegistryData:
    users: Dict[str, UserMetadata] = field(default_factory=dict)
    total_reports: int = 0

    def to_dict(self):
        return {
            "users": {uid: user.to_dict() for uid, user in self.users.items()},
            "total_reports": self.total_reports
        }

    @classmethod
    def from_dict(cls, data):
        users = {uid: UserMetadata.from_dict(u) for uid, u in data.get("users", {}).items()}
        return cls(users=users, total_reports=data.get("total_reports", 0))
