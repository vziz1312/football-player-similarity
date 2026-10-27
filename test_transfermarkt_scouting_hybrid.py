import io
import sqlite3
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import transfermarkt_scouting_hybrid as hybrid


def test_accent_insensitive_matching():
    assert (
        hybrid.normalize_name("Kylian Mbappé")
        == hybrid.normalize_name("kylian mbappe")
    )


def test_uppercase_and_accents():
    assert hybrid.normalize_name("BÉRGSON") == hybrid.normalize_name("bergson")


def test_whitespace():
    assert (
        hybrid.normalize_name("  Lionel Messi  ")
        == hybrid.normalize_name("lionel messi")
    )


def test_empty_name():
    assert hybrid.normalize_name("") == ""


def test_mismatched_vectors():
    try:
        hybrid.calculate_similarity([1, 2], [1])
    except ValueError:
        return

    raise AssertionError("Expected ValueError for mismatched vectors.")


def test_identical_vectors():
    assert hybrid.calculate_similarity([0.5, 0.3], [0.5, 0.3]) == 1.0


def test_sample_size_adjustment():
    player = {
        "appearances": 20,
        "goals": 20,
        "assists": 10,
    }
    baseline_rates = [0.2, 0.1]

    result = hybrid.make_vector(player, baseline_rates)

    assert abs(result[0] - 0.6) < 1e-9
    assert abs(result[1] - 0.3) < 1e-9


def create_test_database(db_path, players, performances):
    """Create an isolated SQLite database and always close it."""
    connection = sqlite3.connect(db_path)

    try:
        connection.execute("""
            CREATE TABLE players (
                player_id INTEGER PRIMARY KEY,
                player_name TEXT NOT NULL,
                main_position TEXT,
                position TEXT
            )
        """)

        connection.execute("""
            CREATE TABLE performances (
                player_id INTEGER NOT NULL,
                season_name TEXT,
                nb_on_pitch INTEGER,
                goals REAL,
                assists REAL,
                penalty_goals REAL,
                yellow_cards REAL
            )
        """)

        connection.executemany(
            "INSERT INTO players VALUES (?, ?, ?, ?)",
            players,
        )

        connection.executemany(
            "INSERT INTO performances VALUES (?, ?, ?, ?, ?, ?, ?)",
            performances,
        )

        connection.commit()
    finally:
        connection.close()

def test_recent_season_mode_and_position_filter():
    players = [
        (1, "Kylian Mbappé (1)", "Attack", "Forward"),
        (2, "Candidate Forward (2)", "Attack", "Forward"),
        (3, "Defender Candidate (3)", "Defender", "Defender"),
    ]

    performances = [
        (1, "25/26", 25, 20, 5, 2, 1),
        (2, "24/25", 25, 18, 4, 1, 2),
        (3, "25/26", 40, 1, 5, 0, 1),
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "recent_test.db"
        create_test_database(db_path, players, performances)

        output = io.StringIO()

        with patch.object(hybrid, "DB_PATH", db_path):
            with redirect_stdout(output):
                results = hybrid.find_similar_players(
                    "kylian mbappe",
                    min_recent_appearances=20,
                    min_career_appearances=100,
                )

        assert "Comparison mode: recent seasons" in output.getvalue()
        assert len(results) == 1
        assert results[0]["name"] == "Candidate Forward (2)"
        assert results[0]["appearances"] == 25
        assert all(
            result["name"] != "Kylian Mbappé (1)"
            for result in results
        )


def test_career_wide_fallback():
    players = [
        (1, "Test Target (1)", "Attack", "Forward"),
        (2, "Career Candidate (2)", "Attack", "Forward"),
        (3, "Defender (3)", "Defender", "Defender"),
    ]

    performances = [
        # The target has only 10 recent appearances.
        (1, "24/25", 10, 5, 1, 0, 0),
        (1, "22/23", 90, 30, 15, 2, 3),

        # Career total: 120 appearances.
        (2, "24/25", 20, 8, 2, 1, 1),
        (2, "22/23", 100, 40, 10, 3, 5),

        # A different position should not enter the result.
        (3, "22/23", 100, 10, 20, 0, 2),
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "career_test.db"
        create_test_database(db_path, players, performances)

        output = io.StringIO()

        with patch.object(hybrid, "DB_PATH", db_path):
            with redirect_stdout(output):
                results = hybrid.find_similar_players(
                    "Test Target",
                    min_recent_appearances=20,
                    min_career_appearances=100,
                )

        message = output.getvalue()

        assert "Falling back to career-wide statistics" in message
        assert len(results) == 1
        assert results[0]["name"] == "Career Candidate (2)"
        assert results[0]["appearances"] == 120
        assert results[0]["goals"] == 48
        assert all(
            result["name"] != "Test Target (1)"
            for result in results
        )


if __name__ == "__main__":
    tests = [
        test_accent_insensitive_matching,
        test_uppercase_and_accents,
        test_whitespace,
        test_empty_name,
        test_mismatched_vectors,
        test_identical_vectors,
        test_sample_size_adjustment,
        test_recent_season_mode_and_position_filter,
        test_career_wide_fallback,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print(f"\nAll {len(tests)} hybrid model tests passed!")