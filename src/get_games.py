# src/get_games.py
"""
Fetch NCAA men's basketball game IDs for a given date range.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

from tqdm import tqdm

from config.settings import (
    ESPN_BASE_URL,
    RAW_DIR,
)
from src.http_client import get as rate_limited_get
from src.progress import PROGRESS_KWARGS

logger = logging.getLogger(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def _date_range(start: str, end: str):
    """Yield every date between start and end."""
    cur = date.fromisoformat(start)
    stop = date.fromisoformat(end)
    while cur <= stop:
        yield cur
        cur += timedelta(days=1)


# ── ESPN API ─────────────────────────────────────────────────────────────

def _fetch_scoreboard_espn(game_date: date) -> list[dict]:
    url = f"{ESPN_BASE_URL}/mens-college-basketball/scoreboard"
    params = {
        "dates": game_date.strftime("%Y%m%d"),
        "groups": 50,
        "limit": 200,
    }

    try:
        r = rate_limited_get(url, params=params, timeout=15)
        if r.status_code == 429:
            logger.warning("ESPN returned 429 Too Many Requests for %s", game_date)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        logger.warning("ESPN scoreboard failed for %s: %s", game_date, exc)
        return []

    games = []
    for event in data.get("events", []):
        gid = str(event.get("id", ""))
        comps = event.get("competitions", [{}])[0]
        competitors = {
            c["homeAway"]: c.get("team", {}).get("displayName", "")
            for c in comps.get("competitors", [])
        }
        if gid:
            games.append(
                {
                    "game_id": gid,
                    "date": game_date.isoformat(),
                    "home_team": competitors.get("home", ""),
                    "away_team": competitors.get("away", ""),
                    "source": "espn",
                }
            )
    return games


# ── public API ────────────────────────────────────────────────────────────────

def _games_for_date(game_date: date, cache: bool) -> tuple[date, list[dict]]:
    cache_path = Path(RAW_DIR) / f"scoreboard_{game_date.isoformat()}.json"
    if cache and cache_path.exists():
        with cache_path.open() as f:
            day_games = json.load(f)
        logger.debug("%s: %d games (cached)", game_date, len(day_games))
        return game_date, day_games

    day_games = _fetch_scoreboard_espn(game_date)
    logger.debug("%s: %d games", game_date, len(day_games))
    if cache and day_games:
        with cache_path.open("w") as f:
            json.dump(day_games, f, indent=2)
    return game_date, day_games


def get_games(start_date, end_date, cache=True, workers: int = 1, progress: bool = True) -> list[dict]:
    dates = list(_date_range(start_date, end_date))
    workers = max(1, workers)

    if workers == 1:
        all_games = []
        for game_date in tqdm(
            dates,
            desc="Fetching scoreboards",
            unit="date",
            disable=not progress,
            **PROGRESS_KWARGS,
        ):
            _, day_games = _games_for_date(game_date, cache)
            all_games.extend(day_games)
        return all_games

    logger.debug("Using %d workers for scoreboard fetching", workers)
    games_by_date = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_games_for_date, game_date, cache): game_date
            for game_date in dates
        }
        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Fetching scoreboards",
            unit="date",
            disable=not progress,
            **PROGRESS_KWARGS,
        ):
            game_date = futures[future]
            try:
                result_date, day_games = future.result()
            except Exception as exc:
                logger.warning("Scoreboard fetch failed for %s: %s", game_date, exc)
                result_date, day_games = game_date, []
            games_by_date[result_date] = day_games

    all_games = []
    for game_date in dates:
        all_games.extend(games_by_date.get(game_date, []))
    return all_games


# ── CLI  ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, pprint

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Fetch NCAA game IDs")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end",   required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    games = get_games(args.start, args.end)
    print(f"\nTotal games fetched: {len(games)}")
    pprint.pprint(games[:5])
