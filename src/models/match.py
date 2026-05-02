from dataclasses import dataclass, asdict

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
