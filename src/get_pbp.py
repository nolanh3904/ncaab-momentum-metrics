# src/get_pbp.py
"""
Fetch and normalize play-by-play data for a single NCAA game via ESPN.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from config.settings import ESPN_BASE_URL, RAW_DIR
from src.http_client import get as rate_limited_get

logger = logging.getLogger(__name__)


# ── Data model ────────────────────────────────────────────────────────────────

class PlayEvent:
    __slots__ = ("game_id", "period", "clock", "team", "points", "description")

    def __init__(self, game_id, period, clock, team, points, description):
        self.game_id     = game_id
        self.period      = period
        self.clock       = clock
        self.team        = team
        self.points      = points
        self.description = description

    def to_dict(self):
        return {
            "game_id": self.game_id, "period": self.period,
            "clock": self.clock, "team": self.team,
            "points": self.points, "description": self.description,
        }


# ── Point inference ───────────────────────────────────────────────────────────

_THREE  = re.compile(r"three|3-pt|3pt|3 point", re.I)
_FREE   = re.compile(r"free throw|foul shot", re.I)
_MADE   = re.compile(r"\bmade\b|\bgood\b|\bscored\b", re.I)
_MISSED = re.compile(r"\bmiss|\bno good\b", re.I)

def _infer_points(description: str, explicit_points=None) -> int:
    if explicit_points is not None:
        return int(explicit_points)
    desc = description or ""
    if _MISSED.search(desc): return 0
    if _FREE.search(desc):   return 1 if _MADE.search(desc) else 0
    if _THREE.search(desc):  return 3 if _MADE.search(desc) else 0
    if _MADE.search(desc):   return 2
    return 0


# ── ESPN parser ───────────────────────────────────────────────────────────────

def _parse_espn(game_id: str, raw: dict) -> list[PlayEvent]:
    events = []

    id_to_name = {}
    try:
        competitors = raw["header"]["competitions"][0]["competitors"]
        for c in competitors:
            id_to_name[c["id"]] = c["team"]["displayName"]
    except (KeyError, IndexError):
        pass

    for play in raw.get("plays", []):
        if not play.get("scoringPlay", False):
            continue
        period      = play.get("period", {}).get("number", 0)
        clock       = play.get("clock", {}).get("displayValue", "")
        desc        = play.get("text", "")
        score_value = play.get("scoreValue") or _infer_points(desc)
        team_id     = play.get("team", {}).get("id", "")
        team_name   = id_to_name.get(team_id, team_id)

        if score_value > 0 and team_name:
            events.append(PlayEvent(
                game_id=game_id, period=period, clock=clock,
                team=team_name, points=score_value, description=desc,
            ))
    return events


# ── Fetch ─────────────────────────────────────────────────────────────────────

def _fetch_espn(game_id: str):
    url = f"{ESPN_BASE_URL}/mens-college-basketball/summary"
    try:
        r = rate_limited_get(url, params={"event": game_id}, timeout=20)
        if r.status_code == 429:
            logger.warning("ESPN returned 429 Too Many Requests for game %s", game_id)
        r.raise_for_status()
        raw = r.json()
        return _parse_espn(game_id, raw), raw
    except Exception as exc:
        logger.warning("ESPN PBP failed for game %s: %s", game_id, exc)
        return None, None


# ── Public API ────────────────────────────────────────────────────────────────

def get_pbp(game_id: str, cache: bool = True) -> list[PlayEvent]:
    cache_path = Path(RAW_DIR) / f"pbp_{game_id}.json"

    if cache and cache_path.exists():
        with cache_path.open() as f:
            raw = json.load(f)
        events = _parse_espn(game_id, raw)
        logger.debug("Game %s: %d scoring events (cached)", game_id, len(events))
        return events

    events, raw = _fetch_espn(game_id)

    if not events:
        logger.error("Could not fetch PBP for game %s", game_id)
        return []

    if cache and raw:
        with cache_path.open("w") as f:
            json.dump(raw, f, indent=2)

    logger.debug("Game %s: %d scoring events", game_id, len(events))
    return events
