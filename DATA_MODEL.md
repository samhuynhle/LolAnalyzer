# LolAnalyzer Data Models

This document outlines the JSON schemas and storage architecture used by the LolAnalyzer application. The system follows a partitioned NoSQL-style design to ensure scalability and performance.

## 1. Directory Structure

```text
data/
├── registry.json           # Central user index (Master Table)
├── matches/                # Detailed game stats (Partitioned by player)
│   └── {player_slug}.json
└── reports/                # Analysis run history (Partitioned by player)
    └── {player_slug}.json
```

---

## 2. Registry (`data/registry.json`)

The Master Table that tracks all players analyzed by the system.

| Field | Type | Description |
| :--- | :--- | :--- |
| `users` | `Object` | Map of `user_id` to User Metadata. |
| `total_reports` | `Integer` | Global count of all analysis runs performed. |

### User Metadata Object
Key: `user_id` (lowercase "name#tag")

```json
{
    "name": "Spear Shot",
    "tag": "1111",
    "region": "europe",
    "first_seen": "YYYY-MM-DD HH:MM:SS",
    "last_analysis": "YYYY-MM-DD HH:MM:SS",
    "match_history_file": "matches/spear_shot_1111.json",
    "report_history_file": "reports/spear_shot_1111.json"
}
```

---

## 3. Match History (`data/matches/{player_slug}.json`)

Granular performance data for every unique game processed. Keyed by `match_id` for automatic deduplication.

| Field | Type | Description |
| :--- | :--- | :--- |
| `match_id` | `String` | Unique Riot Match ID (e.g., "EUW1_12345"). |
| `champion` | `String` | Name of the champion played. |
| `role` | `String` | Position played (TOP, JUNGLE, etc.). |
| `win` | `Boolean` | Outcome of the match. |
| `kills` | `Integer` | Number of kills. |
| `deaths` | `Integer` | Number of deaths. |
| `assists` | `Integer` | Number of assists. |
| `gold` | `Integer` | Total gold earned. |
| `damage` | `Integer` | Total damage dealt to champions. |
| `timestamp` | `String` | Game creation time (YYYY-MM-DD HH:MM:SS). |

**Sorting:** Maintained in descending chronological order (Newest first).

---

## 4. Report History (`data/reports/{player_slug}.json`)

A log of every analysis run performed for a specific player. Keyed by `report_id`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `report_id` | `String` | Unique UUID (v4) for the run. |
| `timestamp` | `String` | Time of the analysis run. |
| `file_path` | `String` | Local path to the generated text report. |
| `match_count_requested` | `Integer` | Number of matches requested in the CLI. |
| `matches_processed` | `Integer` | Number of valid CLASSIC matches found and analyzed. |

**Sorting:** Maintained in descending chronological order (Newest first).
