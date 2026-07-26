"""Pull daily candlestick history for the LeBron-to-Philly Kalshi market."""
import json
from pathlib import Path

import requests

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
SERIES_TICKER = "KXNEXTTEAMNBA"
MARKET_TICKER = "KXNEXTTEAMNBA-26LJAM-PHI"

START_TS = 1783036800  # 2026-07-03T00:00:00Z
END_TS = 1784937600    # 2026-07-25T00:00:00Z
PERIOD_INTERVAL = 1440  # daily candles, in minutes

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "kalshi_candlesticks.json"


def fetch_candlesticks() -> dict:
    url = f"{BASE_URL}/series/{SERIES_TICKER}/markets/{MARKET_TICKER}/candlesticks"
    params = {
        "start_ts": START_TS,
        "end_ts": END_TS,
        "period_interval": PERIOD_INTERVAL,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    data = fetch_candlesticks()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, indent=2))
    print(f"Wrote {len(data.get('candlesticks', []))} candles to {OUT_PATH}")


if __name__ == "__main__":
    main()
