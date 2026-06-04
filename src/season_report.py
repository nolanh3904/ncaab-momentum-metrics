# src/season_report.py
from __future__ import annotations
import csv, json, logging
from collections import defaultdict
from pathlib import Path
from config.settings import OUTPUT_DIR, TEAM_SEEDS_2026, SEED_WEIGHTS
from src.metrics import TeamGameMetrics

logger = logging.getLogger(__name__)

MIN_GAMES = 3


def _base_aggregate(game_metrics: list[TeamGameMetrics]) -> dict:
    buckets = defaultdict(lambda: {
        "team": "", "games": 0,
        "runPointsFor": 0, "runPointsAgainst": 0,
        "largestRun": 0, "largestRunAgainst": 0,
        "numRuns": 0, "numOpponentRuns": 0,
    })
    for m in game_metrics:
        b = buckets[m.team]
        b["team"]              = m.team
        b["games"]             += 1
        b["runPointsFor"]      += m.runPointsFor
        b["runPointsAgainst"]  += m.runPointsAgainst
        b["largestRun"]        = max(b["largestRun"],        m.largestRun)
        b["largestRunAgainst"] = max(b["largestRunAgainst"], m.largestRunAgainst)
        b["numRuns"]           += m.numRuns
        b["numOpponentRuns"]   += m.numOpponentRuns
    return buckets


def aggregate(game_metrics: list[TeamGameMetrics], sort_by: str = "adjRunScore") -> list[dict]:
    buckets = _base_aggregate(game_metrics)

    # ── Seed weighted adjusted diff ───────────────────────────────────────────
    # For each game, weight run differential by opponent's seed weight
    adj_buckets = defaultdict(lambda: {"weighted_diff": 0.0, "weight_sum": 0.0})

    games_map = defaultdict(list)
    for m in game_metrics:
        games_map[m.game_id].append(m)

    for game_id, game_ms in games_map.items():
        if len(game_ms) < 2:
            continue
        for m in game_ms:
            opp_seed   = TEAM_SEEDS_2026.get(m.opponent)
            weight     = SEED_WEIGHTS.get(opp_seed, 0.1) if opp_seed else 0.1
            game_diff  = m.runPointsFor - m.runPointsAgainst
            adj_buckets[m.team]["weighted_diff"] += game_diff * weight
            adj_buckets[m.team]["weight_sum"]    += weight

    # ── Build rows ────────────────────────────────────────────────────────────
    rows = []
    for team, b in buckets.items():
        games   = b["games"]
        rpFor   = b["runPointsFor"]
        rpAg    = b["runPointsAgainst"]
        numRuns = b["numRuns"]
        numOpp  = b["numOpponentRuns"]
        avgRun  = round(rpFor / numRuns, 2) if numRuns else 0.0
        avgAg   = round(rpAg  / numOpp,  2) if numOpp  else 0.0
        avgRunDiff    = round(avgRun - avgAg, 2)
        rpDiffPerGame = round((rpFor - rpAg) / games, 2) if games else 0.0

        adj = adj_buckets[team]
        adjDiffPerGame = round(
            adj["weighted_diff"] / adj["weight_sum"], 2
        ) if adj["weight_sum"] > 0 else rpDiffPerGame

        # Avg opponent seed
        opp_seeds = [
            TEAM_SEEDS_2026.get(m.opponent)
            for m in game_metrics
            if m.team == team and TEAM_SEEDS_2026.get(m.opponent)
        ]
        avgOppSeed = round(sum(opp_seeds) / len(opp_seeds), 1) if opp_seeds else 0.0

        rows.append({
            "team":             team,
            "games":            games,
            "runPointsFor":     rpFor,
            "runPointsAgainst": rpAg,
            "runPointDiff":     rpFor - rpAg,
            "largestRun":       b["largestRun"],
            "largestRunAgainst":b["largestRunAgainst"],
            "numRuns":          numRuns,
            "avgRunSize":       avgRun,
            "numOpponentRuns":  numOpp,
            "avgRunAgainst":    avgAg,
            "avgRunDiff":       avgRunDiff,
            "runsPerGame":      round(numRuns / games, 2) if games else 0.0,
            "rpForPerGame":     round(rpFor / games, 2)   if games else 0.0,
            "rpDiffPerGame":    rpDiffPerGame,
            "adjDiffPerGame":   adjDiffPerGame,
            "avgOppSeed":       avgOppSeed,
            "adjRunScore":      0.0,  # filled below
        })

    # ── Min games filter ──────────────────────────────────────────────────────
    rows = [r for r in rows if r["games"] >= MIN_GAMES]

    # ── Normalize into adjRunScore ────────────────────────────────────────────
    max_adj     = max((r["adjDiffPerGame"] for r in rows), default=1) or 1
    max_avgDiff = max((r["avgRunDiff"]     for r in rows), default=1) or 1

    for r in rows:
        norm_adj = r["adjDiffPerGame"] / max_adj
        norm_avg = r["avgRunDiff"]     / max_avgDiff
        confidence = min(r["games"] / 20, 1.0)
        r["adjRunScore"] = round((0.7 * norm_adj + 0.3 * norm_avg) * confidence, 3)

    rows.sort(key=lambda r: r[sort_by], reverse=True)
    return rows


_FIELDS = [
    "team", "games",
    "runPointsFor", "runPointsAgainst", "runPointDiff",
    "largestRun", "largestRunAgainst",
    "numRuns", "avgRunSize",
    "numOpponentRuns", "avgRunAgainst", "avgRunDiff",
    "runsPerGame", "rpForPerGame", "rpDiffPerGame",
    "adjDiffPerGame", "avgOppSeed", "adjRunScore",
]


def build_season_report(game_metrics, tag="season", sort_by="adjRunScore") -> list[dict]:
    rows = aggregate(game_metrics, sort_by=sort_by)
    out  = Path(OUTPUT_DIR)
    with (out / f"{tag}_run_metrics.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with (out / f"{tag}_run_metrics.json").open("w") as f:
        json.dump(rows, f, indent=2)
    logger.info("Outputs written to %s", out)
    return rows


def print_leaderboard(rows: list[dict], n: int = 25) -> None:
    header = (
        f"{'Rank':<5} {'Team':<30} {'G':>4} "
        f"{'RPDiff':>7} {'Diff/G':>7} {'AdjD/G':>7} "
        f"{'MaxRun':>7} {'MaxAg':>6} {'Runs':>6} "
        f"{'AvgRun':>7} {'AvgAg':>7} {'AvgDiff':>8} "
        f"{'R/G':>6} {'OppSeed':>8} {'AdjScore':>9}"
    )
    print(header)
    print("-" * len(header))

    for rank, row in enumerate(rows[:n], start=1):
        print(
            f"{rank:<5} {row['team']:<30} {row['games']:>4} "
            f"{row['runPointDiff']:>+7} {row['rpDiffPerGame']:>+7.1f} {row['adjDiffPerGame']:>+7.1f} "
            f"{row['largestRun']:>7} {row['largestRunAgainst']:>6} "
            f"{row['numRuns']:>6} "
            f"{row['avgRunSize']:>7.2f} {row['avgRunAgainst']:>7.2f} "
            f"{row['avgRunDiff']:>+8.2f} "
            f"{row['runsPerGame']:>6.2f} {row['avgOppSeed']:>8.1f} {row['adjRunScore']:>9.3f}"
        )
