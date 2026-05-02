from dataclasses import dataclass, field
from typing import Dict
from src.models.user import UserMetadata

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
