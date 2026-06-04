# src/runs.py
"""
run detection algorithm.

A run is an uninterrupted sequence of points scored by one team
without the opponent scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from config.settings import MIN_RUN_SIZE


# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Run:
    """One uninterrupted scoring run by a single team."""
    team:        str
    points:      int
    num_plays:   int
    period:      int
    start_clock: str = ""
    end_clock:   str = ""

    def __repr__(self):
        return (
            f"Run(team={self.team!r}, pts={self.points}, "
            f"plays={self.num_plays}, period={self.period})"
        )


@dataclass
class GameRuns:
    """All runs extracted from a single game, indexed by team."""
    game_id:     str
    home_team:   str = ""
    away_team:   str = ""
    runs:        List[Run] = field(default_factory=list)

    def runs_for(self, team: str) -> List[Run]:
        return [r for r in self.runs if r.team == team]

    def teams(self) -> list[str]:
        return list({r.team for r in self.runs})


# ─────────────────────────────────────────────────────────────────────────────
# Detection engine
# ─────────────────────────────────────────────────────────────────────────────

def detect_runs(events, game_id: str = "", min_run: int = MIN_RUN_SIZE) -> GameRuns:
    result = GameRuns(game_id=game_id)

    if not events:
        return result

    # ── seed with the first event ─────────────────────────────────────────────
    current_team   = events[0].team
    current_points = events[0].points
    current_plays  = 1
    current_period = events[0].period
    start_clock    = events[0].clock

    def _flush(end_clock: str = ""):
        """Save the in progress run if it meets the minimum threshold."""
        if current_points >= min_run:
            result.runs.append(
                Run(
                    team        = current_team,
                    points      = current_points,
                    num_plays   = current_plays,
                    period      = current_period,
                    start_clock = start_clock,
                    end_clock   = end_clock,
                )
            )

    # ── walk the rest of the events ───────────────────────────────────────────
    for event in events[1:]:
        if event.team == current_team:
            # Continuing the same team's run
            current_points += event.points
            current_plays  += 1
        else:
            # Opponent scored flush current run, start new one
            _flush(end_clock=event.clock)

            current_team   = event.team
            current_points = event.points
            current_plays  = 1
            current_period = event.period
            start_clock    = event.clock

    _flush()

    # ── team names ─────────────────────────────────────────────────────
    teams = result.teams()
    if len(teams) >= 2:
        result.home_team = teams[0]
        result.away_team = teams[1]
    elif len(teams) == 1:
        result.home_team = teams[0]

    return result
