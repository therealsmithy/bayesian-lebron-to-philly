"""Flatten raw Reddit post JSON into a daily-level CSV for stance labeling."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "data" / "raw" / "reddit_posts.json"
OUT_PATH = ROOT / "data" / "processed" / "reddit_posts.csv"

COLUMNS = ["id", "subreddit", "created_utc", "title", "selftext", "score", "num_comments", "permalink"]


def main() -> None:
    raw = json.loads(IN_PATH.read_text())

    rows = []
    for p in raw:
        rows.append({
            "id": p.get("id"),
            "subreddit": p.get("subreddit"),
            "created_utc": p.get("created_utc"),
            "title": p.get("title", ""),
            "selftext": p.get("selftext", ""),
            "score": p.get("score", 0),
            "num_comments": p.get("num_comments", 0),
            "permalink": p.get("permalink", ""),
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