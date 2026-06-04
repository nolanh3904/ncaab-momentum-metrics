# tests/test_runs.py
"""
Unit tests for the run detection algorithm and metrics computation.

Run with:  python -m pytest tests/ -v
"""

import pytest
from unittest.mock import MagicMock

from src.runs import detect_runs, Run, GameRuns
from src.metrics import compute_metrics, TeamGameMetrics


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_event(team: str, points: int, period: int = 1, clock: str = "10:00"):
    e = MagicMock()
    e.team    = team
    e.points  = points
    e.period  = period
    e.clock   = clock
    return e


def make_events(seq: list[tuple[str, int]]) -> list:
    """Build event list from (team, pts) tuples."""
    return [make_event(team, pts) for team, pts in seq]


# ─────────────────────────────────────────────────────────────────────────────
# Run detection tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDetectRuns:

    def test_empty_events(self):
        gr = detect_runs([], game_id="empty")
        assert gr.runs == []

    def test_single_team_single_run(self):
        events = make_events([("Duke", 2), ("Duke", 3), ("Duke", 2)])
        gr = detect_runs(events, game_id="g1", min_run=4)
        assert len(gr.runs) == 1
        assert gr.runs[0].team   == "Duke"
        assert gr.runs[0].points == 7

    def test_alternating_teams_no_runs(self):
        """When teams alternate every possession, no run >= 4 is produced."""
        events = make_events([
            ("Duke", 2), ("UNC", 2), ("Duke", 2), ("UNC", 2),
        ])
        gr = detect_runs(events, game_id="g2", min_run=4)
        assert gr.runs == []

    def test_two_runs_same_team(self):
        events = make_events([
            ("Duke", 3), ("Duke", 2),       # run of 5
            ("UNC",  2), ("UNC",  2),       # breaks Duke's run (only 4 = exactly min)
            ("Duke", 3), ("Duke", 3),       # run of 6
        ])
        gr = detect_runs(events, game_id="g3", min_run=4)
        duke_runs = gr.runs_for("Duke")
        unc_runs  = gr.runs_for("UNC")
        assert len(duke_runs) == 2
        assert duke_runs[0].points == 5
        assert duke_runs[1].points == 6
        assert len(unc_runs)  == 1
        assert unc_runs[0].points == 4

    def test_min_run_threshold(self):
        """Runs below min_run are discarded."""
        events = make_events([("Duke", 2), ("Duke", 1), ("UNC", 2)])
        # Duke's run = 3, below default min_run=4
        gr = detect_runs(events, game_id="g4", min_run=4)
        assert len(gr.runs_for("Duke")) == 0

    def test_run_at_exactly_min(self):
        """A run equal to min_run IS included."""
        events = make_events([("Duke", 2), ("Duke", 2), ("UNC", 2)])
        gr = detect_runs(events, game_id="g5", min_run=4)
        assert len(gr.runs_for("Duke")) == 1
        assert gr.runs_for("Duke")[0].points == 4

    def test_teams_are_captured(self):
        events = make_events([
            ("Duke", 3), ("Duke", 3),
            ("UNC",  2), ("UNC",  3),
        ])
        gr = detect_runs(events, game_id="g6", min_run=4)
        assert set(gr.teams()) == {"Duke", "UNC"}

    def test_multi_period(self):
        """Runs that span periods (back-to-back events) are still counted."""
        events = [
            make_event("Duke", 3, period=1, clock="00:05"),
            make_event("Duke", 2, period=2, clock="19:55"),
            make_event("UNC",  2, period=2, clock="18:00"),
        ]
        gr = detect_runs(events, game_id="g7", min_run=4)
        assert gr.runs_for("Duke")[0].points == 5


# ─────────────────────────────────────────────────────────────────────────────
# Metrics tests
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeMetrics:

    def _make_game_runs(self, seq: list[tuple[str, int]], game_id="x") -> GameRuns:
        events = make_events(seq)
        return detect_runs(events, game_id=game_id, min_run=4)

    def test_run_points_for(self):
        gr = self._make_game_runs([
            ("Duke", 3), ("Duke", 2),   # run=5
            ("UNC",  2),
            ("Duke", 2), ("Duke", 3),   # run=5
            ("UNC",  2),
        ])
        metrics = {m.team: m for m in compute_metrics(gr)}
        assert metrics["Duke"].runPointsFor == 10

    def test_run_points_against(self):
        gr = self._make_game_runs([
            ("Duke", 3), ("Duke", 2),   # run=5  (Duke for, UNC against)
            ("UNC",  2), ("UNC",  3),   # run=5  (UNC for, Duke against)
        ])
        metrics = {m.team: m for m in compute_metrics(gr)}
        assert metrics["Duke"].runPointsAgainst == 5
        assert metrics["UNC"].runPointsAgainst  == 5

    def test_run_point_diff(self):
        gr = self._make_game_runs([
            ("Duke", 3), ("Duke", 3),   # run=6
            ("UNC",  2), ("UNC",  2),   # run=4
        ])
        metrics = {m.team: m for m in compute_metrics(gr)}
        assert metrics["Duke"].runPointDiff == 6 - 4   # +2
        assert metrics["UNC"].runPointDiff  == 4 - 6   # -2

    def test_largest_run(self):
        gr = self._make_game_runs([
            ("Duke", 3), ("Duke", 3),       # run=6
            ("UNC",  2),
            ("Duke", 2), ("Duke", 2),       # run=4
            ("UNC",  2),
        ])
        metrics = {m.team: m for m in compute_metrics(gr)}
        assert metrics["Duke"].largestRun == 6

    def test_num_runs(self):
        gr = self._make_game_runs([
            ("Duke", 3), ("Duke", 2),   # run1=5
            ("UNC",  2),
            ("Duke", 3), ("Duke", 2),   # run2=5
            ("UNC",  2),
            ("Duke", 2), ("Duke", 2),   # run3=4
        ])
        metrics = {m.team: m for m in compute_metrics(gr)}
        assert metrics["Duke"].numRuns == 3

    def test_avg_run_size(self):
        gr = self._make_game_runs([
            ("Duke", 3), ("Duke", 3),   # run=6
            ("UNC",  2),
            ("Duke", 2), ("Duke", 2),   # run=4
        ])
        metrics = {m.team: m for m in compute_metrics(gr)}
        duke = metrics["Duke"]
        # rpFor=10, numRuns=2 gives avg=5.0
        assert duke.numRuns    == 2
        assert duke.avgRunSize == pytest.approx(5.0)

    def test_no_runs(self):
        """When a team has no qualifying runs, metrics are all zero."""
        # Both teams alternate, never reach min_run=4
        gr = self._make_game_runs([
            ("Duke", 2), ("UNC", 2), ("Duke", 2), ("UNC", 2),
        ])
        metrics = {m.team: m for m in compute_metrics(gr)}
        # Both teams have 0 runs
        for m in metrics.values():
            assert m.runPointsFor == 0
            assert m.numRuns      == 0
            assert m.avgRunSize   == 0.0

    def test_empty_game(self):
        gr = GameRuns(game_id="empty")
        assert compute_metrics(gr) == []


# ─────────────────────────────────────────────────────────────────────────────
# Edge-case tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_single_event(self):
        events = [make_event("Duke", 2)]
        gr = detect_runs(events, min_run=2)
        assert gr.runs_for("Duke")[0].points == 2

    def test_large_run(self):
        events = make_events([("Duke", 3)] * 10)   # 30-point run
        gr = detect_runs(events, min_run=4)
        assert len(gr.runs_for("Duke")) == 1
        assert gr.runs_for("Duke")[0].points == 30

    def test_three_point_plays(self):
        events = make_events([
            ("Duke", 3), ("Duke", 1),   # and-1 style: 4 pts
            ("UNC",  2),
        ])
        gr = detect_runs(events, min_run=4)
        assert gr.runs_for("Duke")[0].points == 4

    def test_free_throw_run(self):
        events = make_events([
            ("Duke", 1), ("Duke", 1), ("Duke", 1), ("Duke", 1),
            ("UNC", 2),
        ])
        gr = detect_runs(events, min_run=4)
        assert gr.runs_for("Duke")[0].points == 4
