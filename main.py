#!/usr/bin/env python3
# main.py
"""
NCAA Run Differential CLI Tool
============================================
"""

from __future__ import annotations

import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from config.settings   import MIN_RUN_SIZE, SEASON_START, SEASON_END
from src.get_games     import get_games
from src.get_pbp       import get_pbp
from src.runs          import detect_runs
from src.metrics       import compute_metrics
from src.progress      import PROGRESS_KWARGS
from src.season_report import build_season_report, print_leaderboard


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Computes NCAA momentum metrics from play-by-play data."
    )
    p.set_defaults(dry_run=False, tag="season", verbose=False)
    p.add_argument("--start",      default=SEASON_START, help="Start date (YYYY-MM-DD)")
    p.add_argument("--end",        default=SEASON_END,   help="End date (YYYY-MM-DD)")
    p.add_argument("--top",        type=int, default=64, help="Teams to show in leaderboard")
    p.add_argument("--min-run",    type=_positive_int, default=MIN_RUN_SIZE, help="Minimum points to count as a run")
    p.add_argument("--refresh",    action="store_true",  help="Fetch fresh data from ESPN")
    p.add_argument("--workers",    type=_positive_int, default=40, help="Parallel workers for scoreboard and play-by-play fetching")
    p.add_argument("--sort", default="adjRunScore", choices=["adjRunScore", "runScore", "runPointDiff", "rpDiffPerGame", "adjDiffPerGame", "avgRunDiff", "runsPerGame"], help="Metric to sort leaderboard by")
    p.add_argument("--tournament", action="store_true",  help="Filter to 2026 March Madness teams only")
    p.add_argument("-v", "--verbose", action="store_true", help="Show detailed per-date and per-game logs")
    return p.parse_args(argv)


def _process_game(
    index: int,
    total: int,
    game: dict,
    cache: bool,
    min_run: int,
    tournament_teams: set[str] | None,
) -> list:
    gid = game["game_id"]
    logging.debug(
        "[%d/%d] Processing game %s (%s vs %s)",
        index,
        total,
        gid,
        game["home_team"],
        game["away_team"],
    )

    events = get_pbp(gid, cache=cache)
    if not events:
        logging.warning("  No events for game %s - skipping.", gid)
        return []

    game_runs = detect_runs(events, game_id=gid, min_run=min_run)
    metrics = compute_metrics(game_runs)
    if tournament_teams is not None:
        metrics = [m for m in metrics if m.team in tournament_teams]
    return metrics


def run_pipeline(args: argparse.Namespace) -> list[dict]:
    cache = not args.refresh
    show_progress = not args.verbose

    # Fetch game IDs
    logging.info("Fetching games from %s to %s", args.start, args.end)
    games = get_games(
        args.start,
        args.end,
        cache=cache,
        workers=args.workers,
        progress=show_progress,
    )
    logging.info("Found %d games.", len(games))

    if not games:
        logging.warning("No games found for the given date range. Exiting.")
        return []

    if args.dry_run:
        print(f"\n{'ID':<20} {'Date':<12} {'Home':<25} {'Away':<25}")
        print("-" * 85)
        for g in games:
            print(f"{g['game_id']:<20} {g['date']:<12} {g['home_team']:<25} {g['away_team']:<25}")
        return []

    # Tournament filter
    if args.tournament:
        from config.settings import MARCH_MADNESS_2026
        before = len(games)
        games = [
            g for g in games
            if g["home_team"] in MARCH_MADNESS_2026 and g["away_team"] in MARCH_MADNESS_2026
        ]
        logging.info("Tournament filter: %d - %d games", before, len(games))
        tournament_teams = MARCH_MADNESS_2026
    else:
        tournament_teams = None

    #  PBP runs metrics
    all_metrics = []
    errors = 0

    if args.workers == 1:
        numbered_games = list(enumerate(games, start=1))
        for i, game in tqdm(
            numbered_games,
            total=len(numbered_games),
            desc="Processing games",
            unit="game",
            disable=not show_progress,
            **PROGRESS_KWARGS,
        ):
            try:
                all_metrics.extend(
                    _process_game(i, len(games), game, cache, args.min_run, tournament_teams)
                )
            except Exception as exc:
                logging.error("  Error processing game %s: %s", game["game_id"], exc)
                errors += 1
    else:
        logging.debug("Using %d workers for play-by-play processing", args.workers)
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(
                    _process_game,
                    i,
                    len(games),
                    game,
                    cache,
                    args.min_run,
                    tournament_teams,
                ): game
                for i, game in enumerate(games, start=1)
            }
            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Processing games",
                unit="game",
                disable=not show_progress,
                **PROGRESS_KWARGS,
            ):
                game = futures[future]
                try:
                    all_metrics.extend(future.result())
                except Exception as exc:
                    logging.error("  Error processing game %s: %s", game["game_id"], exc)
                    errors += 1

    logging.info("Pipeline complete. Games processed: %d, errors: %d", len(games) - errors, errors)

    if not all_metrics:
        logging.warning("No metrics were computed. Check API connectivity or date range.")
        return []

    # Aggregate and write outputs
    rows = build_season_report(all_metrics, tag=args.tag, sort_by=args.sort)

    print(f"\n{'='*60}")
    print(f"  NCAA Run Differential Leaderboard — Top {args.top}")
    print(f"  Date range: {args.start} - {args.end}")
    print(f"  Minimum run: {args.min_run} points")
    print(f"{'='*60}\n")
    print_leaderboard(rows, n=args.top)
    print(f"\nOutputs saved to: data/outputs/{args.tag}_run_metrics.{{csv,json}}")

    return rows


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level   = logging.DEBUG if args.verbose else logging.CRITICAL,
        format  = "%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt = "%H:%M:%S",
    )
    run_pipeline(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
