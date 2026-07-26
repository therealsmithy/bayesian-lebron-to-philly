"""Flatten raw Kalshi candlestick JSON into a daily price CSV."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "data" / "raw" / "kalshi_candlesticks.json"
OUT_PATH = ROOT / "data" / "processed" / "kalshi_daily.csv"


def main() -> None:
    raw = json.loads(IN_PATH.read_text())

    rows = []
    for c in raw["candlesticks"]:
        date = datetime.fromtimestamp(c["end_period_ts"], tz=timezone.utc).date()
        rows.append({
            "date": date,
            "open": float(c["price"]["open_dollars"]),
            "high": float(c["price"]["high_dollars"]),
            "low": float(c["price"]["low_dollars"]),
            "close": float(c["price"]["close_dollars"]),
            "mean": float(c["price"]["mean_dollars"]),
            "volume": float(c["volume_fp"]),
            "open_interest": float(c["open_interest_fp"]),
        })

    df = pd.DataFrame(rows).sort_values("date")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(df)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
