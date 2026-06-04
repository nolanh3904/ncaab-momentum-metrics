# NCAAB Momentum Metrics

Command line tool for computing NCAA men's basketball momentum run metrics from ESPN play-by-play data.

The tool detects scoring runs inside each game, aggregates run differential metrics by team, and writes leaderboard outputs to the terminal as well as CSV and JSON.

## Why?

A new popular statistic in college basketball is the kill shot. A kill shot refers to a team scoring 10 unanswered points in a game. Teams that record at least 1 kill shot in a game have 71% chance to go on and win that game. This makes it a very exciting and powerful statistic. However, the kill shot statistic has its flaws. What if a team goes on a 9-0 run? No kill shot. what if a team goes ona  19-0 run? Just 1 kill shot counted. Basketball is a game of runs and I thought this statistic was too restrictive and wanted a more flexible stat centered around the kill shot statistic. This tool lets the user adjust what counts as a run, and allows the user to look deeper into why the kill shot metric is so effective. By looking into smaller runs, as well as the smaller runs allowed, it helps better distinguish team performance and momentum trends that may be overlooked by the kill shot metric.

## What It Measures

A run is an uninterrupted sequence of points scored by one team before the opponent scores. By default, runs must be at least 4 points, but that threshold can be changed with `--min-run`.

The season report includes metrics such as:

- run points for and against
- run point differential
- largest run and largest run allowed
- number of runs
- average run size
- run differential per game
- seed adjusted run score

## Install

Clone the repository, then install it in editable mode:

```bash
git clone https://github.com/nolanh3904/ncaab-momentum-metrics.git
cd ncaab-momentum-metrics
python3 -m pip install -e .
```

After installation, the CLI is available as:

```bash
ncaab
```

You can check available options with:

```bash
ncaab --help
```

## Basic Usage

Filter to only teams in the tournament:

```bash
ncaab --tournament
```

Use a custom date range:

```bash
ncaab --start 2025-11-04 --end 2026-04-04
```

Change the minimum run size:

```bash
ncaab --min-run 6
```

Fetch fresh data from ESPN instead of using local cache:

```bash
ncaab --refresh
```

Use more or fewer workers:

```bash
ncaab --workers 40
```

Show detailed date and game logs:

```bash
ncaab --verbose
```

## Output

Results are displayed in the terminal and also exported to:

```text
data/outputs/season_run_metrics.csv
data/outputs/season_run_metrics.json
```

## License

This project is released under the MIT License. See `LICENSE` for details.
