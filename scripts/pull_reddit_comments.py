"""Pull Reddit comments mentioning LeBron-to-Philly for the target window.

Uses the Arctic Shift API (a maintained Pushshift successor with unauthenticated
access and no OAuth app approval needed), mirroring pull_reddit.py's approach
but against /api/comments/search with a body keyword filter instead of title.
"""
import json
import time
from pathlib import Path

import requests

ARCTIC_SHIFT_URL = "https://arctic-shift.photon-reddit.com/api/comments/search"

AFTER = "2026-07-03"
BEFORE = "2026-07-25"

SUBREDDITS = ["sixers", "nba", "nbadiscussion"]
BODY_QUERY = "lebron"

HEADERS = {"User-Agent": "bayesian-lebron-to-philly-research/0.1"}

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "reddit_comments.json"


def fetch_page(subreddit: str, after_ts: int, retries: int = 12) -> list[dict]:
    params = {
        "subreddit": subreddit,
        "after": after_ts,
        "before": BEFORE,
        "body": BODY_QUERY,
        "limit": 100,
        "sort": "asc",
    }
    resp = None
    for attempt in range(retries):
        try:
            resp = requests.get(ARCTIC_SHIFT_URL, params=params, headers=HEADERS, timeout=60)
            if resp.ok:
                data = resp.json().get("data")
                if data is not None:
                    return data
        except requests.exceptions.RequestException:
            pass
        if attempt < retries - 1:
            wait = min(10 * (attempt + 1), 60)  # very active subreddits time out easily
            print(f"  retrying r/{subreddit} in {wait}s (attempt {attempt + 1}/{retries})")
            time.sleep(wait)
    if resp is not None:
        resp.raise_for_status()
    raise requests.exceptions.RequestException(f"Failed to fetch r/{subreddit} after {retries} attempts")
    return []


def fetch_subreddit(subreddit: str) -> list[dict]:
    comments = []
    after_ts = AFTER
    while True:
        batch = fetch_page(subreddit, after_ts)
        if not batch:
            break
        comments.extend(batch)
        print(f"  r/{subreddit}: {len(comments)} comments so far (up to {batch[-1]['created_utc']})")
        if len(batch) < 100:
            break
        after_ts = batch[-1]["created_utc"] + 1  # cursor past the last comment
        time.sleep(2)
    return comments


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_comments = []
    for subreddit in SUBREDDITS:
        comments = fetch_subreddit(subreddit)
        print(f"r/{subreddit}: {len(comments)} comments")
        all_comments.extend(comments)
        OUT_PATH.write_text(json.dumps(all_comments, indent=2))  # checkpoint after each subreddit
        time.sleep(2)  # be polite to the free API

    print(f"Wrote {len(all_comments)} comments to {OUT_PATH}")


if __name__ == "__main__":
    main()
