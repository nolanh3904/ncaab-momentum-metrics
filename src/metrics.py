# src/metrics.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from src.runs import GameRuns, Run


@dataclass
class TeamGameMetrics:
    game_id:           str
    team:              str
    opponent:          str
    runPointsFor:      int
    runPointsAgainst:  int
    largestRun:        int
    largestRunAgainst: int
    numRuns:           int
    avgRunSize:        float
    numOpponentRuns:   int
    avgRunAgainst:     float

    @property
    def runPointDiff(self) -> int:
        return self.runPointsFor - self.runPointsAgainst

    @property
    def avgRunDiff(self) -> float:
        return round(self.avgRunSize - self.avgRunAgainst, 2)

    def to_dict(self) -> dict:
        return {
            "game_id":           self.game_id,
            "team":              self.team,
            "opponent":          self.opponent,
            "runPointsFor":      self.runPointsFor,
            "runPointsAgainst":  self.runPointsAgainst,
            "runPointDiff":      self.runPointDiff,
            "largestRun":        self.largestRun,
            "largestRunAgainst": self.largestRunAgainst,
            "numRuns":           self.numRuns,
            "avgRunSize":        round(self.avgRunSize, 2),
            "numOpponentRuns":   self.numOpponentRuns,
            "avgRunAgainst":     round(self.avgRunAgainst, 2),
            "avgRunDiff":        self.avgRunDiff,
        }

    def __repr__(self):
        return (
            f"TeamGameMetrics(team={self.team!r}, "
            f"rpFor={self.runPointsFor}, rpAgainst={self.runPointsAgainst}, "
            f"diff={self.runPointDiff}, largest={self.largestRun}, "
            f"largestAg={self.largestRunAgainst}, runs={self.numRuns}, "
            f"avg={self.avgRunSize:.2f}, avgAg={self.avgRunAgainst:.2f})"
        )


def _metrics_for_team(
    team: str,
    my_runs: List[Run],
    opp_runs: List[Run],
    opponent: str,
    game_id: str,
) -> TeamGameMetrics:
    rpFor            = sum(r.points for r in my_runs)
    rpAgainst        = sum(r.points for r in opp_runs)
    largest          = max((r.points for r in my_runs),  default=0)
    largestAgainst   = max((r.points for r in opp_runs), default=0)
    num              = len(my_runs)
    numOpp           = len(opp_runs)
    avg              = rpFor     / num    if num    else 0.0
    avgAgainst       = rpAgainst / numOpp if numOpp else 0.0

    return TeamGameMetrics(
        game_id           = game_id,
        team              = team,
        opponent          = opponent,
        runPointsFor      = rpFor,
        runPointsAgainst  = rpAgainst,
        largestRun        = largest,
        largestRunAgainst = largestAgainst,
        numRuns           = num,
        avgRunSize        = avg,
        numOpponentRuns   = numOpp,
        avgRunAgainst     = avgAgainst,
    )


def compute_metrics(game_runs: GameRuns) -> list[TeamGameMetrics]:
    teams = game_runs.teams()
    if not teams:
        return []

    results = []
    for team in teams:
        opponents = [t for t in teams if t != team]
        opponent  = opponents[0] if opponents else ""
        my_runs   = game_runs.runs_for(team)
        opp_runs  = game_runs.runs_for(opponent) if opponent else []
        results.append(_metrics_for_team(
            team=team, my_runs=my_runs, opp_runs=opp_runs,
            opponent=opponent, game_id=game_runs.game_id,
        ))

    return results
