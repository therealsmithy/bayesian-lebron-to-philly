"""Pull Reddit posts mentioning LeBron-to-Philly for the target window.

Uses the Arctic Shift API (a maintained Pushshift successor with unauthenticated
access and no OAuth app approval needed). Unlike PullPush, Arctic Shift has this
window indexed as of the time this was written.
"""
import json
import time
from pathlib import Path

import requests

ARCTIC_SHIFT_URL = "https://arctic-shift.photon-reddit.com/api/posts/search"

AFTER = "2026-07-03"
BEFORE = "2026-07-25"

SUBREDDITS = ["sixers", "nba", "nbadiscussion"]
TITLE_QUERY = "lebron"

HEADERS = {"User-Agent": "bayesian-lebron-to-philly-research/0.1"}

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "reddit_posts.json"


def fetch_page(subreddit: str, after_ts: int, retries: int = 12) -> list[dict]:
    params = {
        "subreddit": subreddit,
        "after": after_ts,
        "before": BEFORE,
        "title": TITLE_QUERY,
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


def fetch_subreddit(subreddit: str) -> list[dict]:
    posts = []
    after_ts = AFTER
    while True:
        batch = fetch_page(subreddit, after_ts)
        if not batch:
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        after_ts = batch[-1]["created_utc"] + 1  # cursor past the last post
        time.sleep(2)
    return posts


def main() -> None:
    all_posts = []
    for subreddit in SUBREDDITS:
        posts = fetch_subreddit(subreddit)
        print(f"r/{subreddit}: {len(posts)} posts")
        all_posts.extend(posts)
        time.sleep(2)  # be polite to the free API

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(all_posts, indent=2))
    print(f"Wrote {len(all_posts)} posts to {OUT_PATH}")


if __name__ == "__main__":
    main()