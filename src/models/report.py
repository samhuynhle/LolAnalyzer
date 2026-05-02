from dataclasses import dataclass, asdict

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
