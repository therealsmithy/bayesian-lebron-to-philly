"""Pull daily Google Trends search-interest data for the LeBron-to-Philly window."""
import json
from pathlib import Path

from pytrends.request import TrendReq

TIMEFRAME = "2026-07-03 2026-07-26"
# pytrends allows up to 5 terms per request
KEYWORDS = ["LeBron", "LeBron Philly", "LeBron Sixers", "LeBron 76ers"]

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "google_trends.json"


def main() -> None:
    pytrends = TrendReq(hl="en-US", tz=360)
    pytrends.build_payload(KEYWORDS, timeframe=TIMEFRAME, geo="US")
    df = pytrends.interest_over_time()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(df.reset_index().to_json(orient="records", date_format="iso", indent=2))
    print(f"Wrote {len(df)} rows to {OUT_PATH}")
    print(df.head())


if __name__ == "__main__":
    main()
