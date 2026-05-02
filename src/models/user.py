from dataclasses import dataclass, asdict

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
