from src import get_games as get_games_module


def test_get_games_with_workers_preserves_date_order(monkeypatch):
    def fake_fetch(game_date):
        return [{
            "game_id": game_date.isoformat(),
            "date": game_date.isoformat(),
            "home_team": "Home",
            "away_team": "Away",
            "source": "test",
        }]

    monkeypatch.setattr(get_games_module, "_fetch_scoreboard_espn", fake_fetch)

    games = get_games_module.get_games(
        "2025-01-01",
        "2025-01-03",
        cache=False,
        workers=3,
        progress=False,
    )

    assert [game["date"] for game in games] == [
        "2025-01-01",
        "2025-01-02",
        "2025-01-03",
    ]
