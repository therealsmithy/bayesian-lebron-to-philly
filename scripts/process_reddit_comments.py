"""Flatten raw Reddit comment JSON into a daily-level CSV for stance labeling."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "data" / "raw" / "reddit_comments.json"
OUT_PATH = ROOT / "data" / "processed" / "reddit_comments.csv"

COLUMNS = [
    "id", "subreddit", "created_utc", "body", "score",
    "link_id", "link_title", "parent_id", "permalink",
]


def main() -> None:
    raw = json.loads(IN_PATH.read_text())

    rows = []
    for c in raw:
        rows.append({
            "id": c.get("id"),
            "subreddit": c.get("subreddit"),
            "created_utc": c.get("created_utc"),
            "body": c.get("body", ""),
            "score": c.get("score", 0),
            "link_id": c.get("link_id"),
            "link_title": c.get("link_title", ""),
            "parent_id": c.get("parent_id"),
            "permalink": c.get("permalink", ""),
        })

    df = pd.DataFrame(rows, columns=COLUMNS).drop_duplicates(subset="id")
    df["date"] = df["created_utc"].apply(
        lambda ts: datetime.fromtimestamp(ts, tz=timezone.utc).date()
    )

    df = df.sort_values("date")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(df)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
