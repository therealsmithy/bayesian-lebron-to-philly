"""Pull Reddit comments mentioning LeBron-to-Philly for the target window.

Uses the Arctic Shift API (a maintained Pushshift successor with unauthenticated
access and no OAuth app approval needed), mirroring pull_reddit.py's approach
but against /api/comments/search with a body keyword filter instead of title.

This API is flaky under load, especially on wide time windows against active
subreddits, so this script:
  - checkpoints to disk after every page (resumable if interrupted/crashed)
  - on a persistently failing page, halves the time window and retries each
    half separately, since narrower windows are cheaper for the server
"""
import json
import time
from pathlib import Path

import requests

ARCTIC_SHIFT_URL = "https://arctic-shift.photon-reddit.com/api/comments/search"

AFTER_TS = 1783036800  # 2026-07-03T00:00:00Z
BEFORE_TS = 1784937600  # 2026-07-25T00:00:00Z

SUBREDDITS = ["sixers", "nba", "nbadiscussion"]
BODY_QUERY = "lebron"
MIN_WINDOW_SECONDS = 3600  # give up splitting below 1hr windows

HEADERS = {"User-Agent": "bayesian-lebron-to-philly-research/0.1"}

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "reddit_comments.json"


def fetch_page(subreddit: str, after_ts: int, before_ts: int, retries: int = 8) -> list[dict] | None:
    """Returns the page's data, or None if this window is persistently failing."""
    params = {
        "subreddit": subreddit,
        "after": after_ts,
        "before": before_ts,
        "body": BODY_QUERY,
        "limit": 100,
        "sort": "asc",
    }
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
            wait = min(10 * (attempt + 1), 45)
            print(f"    retrying r/{subreddit} [{after_ts}, {before_ts}) in {wait}s (attempt {attempt + 1}/{retries})")
            time.sleep(wait)
    return None


def fetch_window(subreddit: str, after_ts: int, before_ts: int, on_batch) -> None:
    """Fetches all comments in [after_ts, before_ts), splitting the window on persistent failure."""
    cursor = after_ts
    while cursor < before_ts:
        batch = fetch_page(subreddit, cursor, before_ts)
        if batch is None:
            span = before_ts - cursor
            if span <= MIN_WINDOW_SECONDS:
                print(f"    giving up on r/{subreddit} [{cursor}, {before_ts}) after repeated failures (window too small to split)")
                return
            mid = cursor + span // 2
            print(f"    splitting r/{subreddit} [{cursor}, {before_ts}) at {mid}")
            fetch_window(subreddit, cursor, mid, on_batch)
            fetch_window(subreddit, mid, before_ts, on_batch)
            return
        if not batch:
            return
        on_batch(batch)
        if len(batch) < 100:
            return
        cursor = batch[-1]["created_utc"] + 1
        time.sleep(2)


def load_existing() -> list[dict]:
    if OUT_PATH.exists():
        return json.loads(OUT_PATH.read_text())
    return []


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_comments = load_existing()
    seen_ids = {c["id"] for c in all_comments}
    # resume each subreddit from the max created_utc already collected for it
    resume_from = {}
    for c in all_comments:
        resume_from[c["subreddit"]] = max(resume_from.get(c["subreddit"], 0), c["created_utc"])

    def on_batch(batch: list[dict]) -> None:
        new = [c for c in batch if c["id"] not in seen_ids]
        seen_ids.update(c["id"] for c in new)
        all_comments.extend(new)
        OUT_PATH.write_text(json.dumps(all_comments, indent=2))
        print(f"    +{len(new)} ({len(all_comments)} total) up to {batch[-1]['created_utc']}")

    for subreddit in SUBREDDITS:
        start = resume_from.get(subreddit, AFTER_TS - 1) + 1
        if start >= BEFORE_TS:
            print(f"r/{subreddit}: already complete ({sum(1 for c in all_comments if c['subreddit'] == subreddit)} comments)")
            continue
        print(f"r/{subreddit}: starting from {start}")
        fetch_window(subreddit, start, BEFORE_TS, on_batch)
        print(f"r/{subreddit}: {sum(1 for c in all_comments if c['subreddit'] == subreddit)} comments total")
        time.sleep(2)

    print(f"Wrote {len(all_comments)} comments to {OUT_PATH}")


if __name__ == "__main__":
    main()
