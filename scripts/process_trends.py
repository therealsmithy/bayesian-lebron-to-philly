"""Flatten raw Google Trends JSON into a daily search-interest CSV."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "data" / "raw" / "google_trends.json"
OUT_PATH = ROOT / "data" / "processed" / "trends_daily.csv"


def main() -> None:
    records = json.loads(IN_PATH.read_text())
    df = pd.DataFrame(records)

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.drop(columns=["isPartial"])
    df = df.rename(columns={
        "LeBron": "lebron",
        "LeBron Philly": "lebron_philly",
        "LeBron Sixers": "lebron_sixers",
        "LeBron 76ers": "lebron_76ers",
    })

    df = df.sort_values("date")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(df)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
