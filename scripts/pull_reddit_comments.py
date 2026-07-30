"""Pull comments under the LeBron-to-Philly posts already collected by pull_reddit.py.

Uses the Arctic Shift API, scoped per-post via link_id (a cheap indexed lookup)
rather than a body-keyword full-text search across an entire subreddit, which
proved too expensive for the server on a high-volume subreddit like r/nba
(a prior attempt ran ~13 hours and covered only ~6% of r/nba's date range).

Checkpoints to disk after every post so the pull is resumable.
"""
import json
import time
from pathlib import Path

import requests

ARCTIC_SHIFT_URL = "https://arctic-shift.photon-reddit.com/api/comments/search"

HEADERS = {"User-Agent": "bayesian-lebron-to-philly-research/0.1"}

POSTS_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "reddit_posts.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "reddit_comments.json"


def fetch_page(link_id: str, after_ts: int, retries: int = 8) -> list[dict] | None:
    params = {
        "link_id": link_id,
        "after": after_ts,
        "limit": 100,
        "sort": "asc",
    }
    for attempt in range(retries):
        try:
            resp = requests.get(ARCTIC_SHIFT_URL, params=params, headers=HEADERS, timeout=30)
            if resp.ok:
                data = resp.json().get("data")
                if data is not None:
                    return data
        except requests.exceptions.RequestException:
            pass
        if attempt < retries - 1:
            wait = min(5 * (attempt + 1), 30)
            time.sleep(wait)
    return None


def fetch_post_comments(post: dict) -> list[dict]:
    comments = []
    after_ts = post["created_utc"]
    while True:
        batch = fetch_page(post["id"], after_ts)
        if batch is None:
            print(f"    giving up on post {post['id']} after repeated failures")
            break
        if not batch:
            break
        comments.extend(batch)
        if len(batch) < 100:
            break
        after_ts = batch[-1]["created_utc"] + 1
        time.sleep(0.5)
    return comments


def load_existing() -> tuple[list[dict], set[str]]:
    if OUT_PATH.exists():
        comments = json.loads(OUT_PATH.read_text())
        done_link_ids = {c["link_id"].removeprefix("t3_") for c in comments}
        return comments, done_link_ids
    return [], set()


def main() -> None:
    posts = json.loads(POSTS_PATH.read_text())
    all_comments, done_link_ids = load_existing()

    remaining = [p for p in posts if p["id"] not in done_link_ids]
    print(f"{len(done_link_ids)} posts already done, {len(remaining)} remaining")

    for i, post in enumerate(remaining):
        comments = fetch_post_comments(post)
        all_comments.extend(comments)
        OUT_PATH.write_text(json.dumps(all_comments, indent=2))
        if (i + 1) % 25 == 0 or comments:
            print(f"  [{i + 1}/{len(remaining)}] r/{post['subreddit']} post {post['id']}: "
                  f"+{len(comments)} comments ({len(all_comments)} total)")
        time.sleep(0.5)

    print(f"Wrote {len(all_comments)} comments to {OUT_PATH}")


if __name__ == "__main__":
    main()
