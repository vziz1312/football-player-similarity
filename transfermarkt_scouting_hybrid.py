import sqlite3
import unicodedata
from math import sqrt
from pathlib import Path

DB_PATH = Path(__file__).with_name("transfermarkt.db")

RECENT_SEASONS = ("25/26", "24/25", "23/24")
MIN_RECENT_APPEARANCES = 20
MIN_CAREER_APPEARANCES = 100
PRIOR_APPEARANCES = 20


def normalize_name(value):
    """Normalize names so accents and capitalization do not matter."""
    value = unicodedata.normalize("NFKD", value or "")
    return "".join(
        char for char in value
        if not unicodedata.combining(char)
    ).casefold().strip()


def get_player_stats(connection, player_id, seasons=None):
    """Return aggregated statistics for one player."""
    query = """
        SELECT
            p.player_id,
            p.player_name,
            p.main_position,
            p.position,
            SUM(COALESCE(s.nb_on_pitch, 0)) AS appearances,
            SUM(COALESCE(s.goals, 0)) AS goals,
            SUM(COALESCE(s.assists, 0)) AS assists,
            SUM(COALESCE(s.penalty_goals, 0)) AS penalty_goals,
            SUM(COALESCE(s.yellow_cards, 0)) AS yellow_cards
        FROM players p
        JOIN performances s ON s.player_id = p.player_id
        WHERE s.player_id = ?
    """
    params = [player_id]

    if seasons:
        placeholders = ", ".join("?" for _ in seasons)
        query += f" AND s.season_name IN ({placeholders})"
        params.extend(seasons)

    query += """
        GROUP BY
            p.player_id,
            p.player_name,
            p.main_position,
            p.position
    """

    return connection.execute(query, params).fetchone()


def get_players_stats(connection, seasons=None, min_appearances=100):
    """Return players meeting the minimum-appearances threshold."""
    query = """
        SELECT
            p.player_id,
            p.player_name,
            p.main_position,
            p.position,
            SUM(COALESCE(s.nb_on_pitch, 0)) AS appearances,
            SUM(COALESCE(s.goals, 0)) AS goals,
            SUM(COALESCE(s.assists, 0)) AS assists,
            SUM(COALESCE(s.penalty_goals, 0)) AS penalty_goals,
            SUM(COALESCE(s.yellow_cards, 0)) AS yellow_cards
        FROM players p
        JOIN performances s ON s.player_id = p.player_id
    """
    params = []

    if seasons:
        placeholders = ", ".join("?" for _ in seasons)
        query += f" WHERE s.season_name IN ({placeholders})"
        params.extend(seasons)

    query += """
        GROUP BY
            p.player_id,
            p.player_name,
            p.main_position,
            p.position
        HAVING SUM(COALESCE(s.nb_on_pitch, 0)) >= ?
    """
    params.append(min_appearances)

    return connection.execute(query, params).fetchall()


def make_vector(player, baseline_rates):
    """
    Build a goals/assists-per-appearance vector.

    Players with fewer appearances are adjusted more strongly
    toward the pooled average rates for their position.
    """
    appearances = player["appearances"]

    if appearances is None or appearances <= 0:
        raise ValueError("Player must have positive appearances.")

    if len(baseline_rates) != 2:
        raise ValueError("Expected two baseline rates.")

    observed_rates = [
        player["goals"] / appearances,
        player["assists"] / appearances,
    ]

    reliability = appearances / (
        appearances + PRIOR_APPEARANCES
    )

    return [
        reliability * observed + (1 - reliability) * baseline
        for observed, baseline in zip(observed_rates, baseline_rates)
    ]


def calculate_similarity(vector1, vector2):
    """Convert Euclidean distance into a bounded ranking score."""
    if len(vector1) != len(vector2):
        raise ValueError("Vectors must have the same length.")

    distance = sqrt(
        sum((a - b) ** 2 for a, b in zip(vector1, vector2))
    )

    return 1 / (1 + distance)


def same_position(candidate, target):
    """Check whether two players share the target's position category."""
    if target["main_position"]:
        return candidate["main_position"] == target["main_position"]

    if target["position"]:
        return candidate["position"] == target["position"]

    return False


def calculate_position_baseline(position_rows):
    """Calculate pooled goals and assists per appearance."""
    total_appearances = sum(
        row["appearances"] for row in position_rows
    )

    if total_appearances <= 0:
        raise ValueError("No appearances available for the position baseline.")

    total_goals = sum(row["goals"] for row in position_rows)
    total_assists = sum(row["assists"] for row in position_rows)

    return [
        total_goals / total_appearances,
        total_assists / total_appearances,
    ]


def find_similar_players(
    player_name,
    limit=10,
    min_recent_appearances=MIN_RECENT_APPEARANCES,
    min_career_appearances=MIN_CAREER_APPEARANCES,
):
    """Find players with similar attacking production."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.create_function("NORMALIZE_NAME", 1, normalize_name)

    try:
        name = player_name.strip()

        target = connection.execute(
            """
            SELECT player_id, player_name, main_position, position
            FROM players
            WHERE NORMALIZE_NAME(TRIM(player_name)) =
                  NORMALIZE_NAME(TRIM(?))
               OR NORMALIZE_NAME(TRIM(player_name)) LIKE
                  NORMALIZE_NAME(TRIM(?))
            ORDER BY
                CASE
                    WHEN NORMALIZE_NAME(TRIM(player_name)) =
                         NORMALIZE_NAME(TRIM(?))
                    THEN 0
                    ELSE 1
                END
            LIMIT 1
            """,
            (name, f"{name} (%)", name),
        ).fetchone()

        if target is None:
            print(f"Player not found: {name}")
            return []

        recent_target = get_player_stats(
            connection,
            target["player_id"],
            RECENT_SEASONS,
        )

        # Use recent data when the target has enough recent appearances.
        if (
            recent_target is not None
            and recent_target["appearances"] >= min_recent_appearances
        ):
            target_stats = recent_target
            candidate_rows = get_players_stats(
                connection,
                seasons=RECENT_SEASONS,
                min_appearances=min_recent_appearances,
            )
            print("Comparison mode: recent seasons (25/26, 24/25, 23/24)")

        else:
            target_stats = get_player_stats(
                connection,
                target["player_id"],
            )

            recent_apps = (
                recent_target["appearances"]
                if recent_target is not None
                else 0
            )

            print(
                f"Target has only {recent_apps:g} recorded appearances "
                "in the selected recent seasons."
            )
            print(
                "Falling back to career-wide statistics for both "
                "the target and candidates."
            )

            if (
                target_stats is None
                or target_stats["appearances"] < min_career_appearances
            ):
                print(
                    "Not enough career appearances for a reliable comparison."
                )
                return []

            candidate_rows = get_players_stats(
                connection,
                min_appearances=min_career_appearances,
            )

        # Restrict both the baseline and rankings to the same position.
        position_rows = [
            row for row in candidate_rows
            if same_position(row, target_stats)
        ]

        if not position_rows:
            print("No candidates available for the target's position.")
            return []

        try:
            position_rates = calculate_position_baseline(position_rows)
        except ValueError as error:
            print(str(error))
            return []

        target_vector = make_vector(target_stats, position_rates)
        results = []

        for candidate in position_rows:
            if candidate["player_id"] == target["player_id"]:
                continue

            candidate_vector = make_vector(candidate, position_rates)

            similarity = calculate_similarity(
                target_vector,
                candidate_vector,
            )

            appearances = candidate["appearances"]

            results.append({
                "name": candidate["player_name"],
                "position": (
                    candidate["main_position"] or candidate["position"]
                ),
                "appearances": appearances,
                "goals": candidate["goals"],
                "assists": candidate["assists"],
                "penalty_goals": candidate["penalty_goals"],
                "yellow_cards": candidate["yellow_cards"],
                "goals_per_app": candidate["goals"] / appearances,
                "assists_per_app": candidate["assists"] / appearances,
                "adjusted_goals_per_app": candidate_vector[0],
                "adjusted_assists_per_app": candidate_vector[1],
                "similarity": similarity,
            })

        results.sort(
            key=lambda player: player["similarity"],
            reverse=True,
        )

        print(f"Target: {target_stats['player_name']}")
        print(
            "Target appearances in comparison period: "
            f"{target_stats['appearances']:g}"
        )
        print("Features: goals and assists per appearance.")
        print(
            f"Sample-size adjustment: {PRIOR_APPEARANCES} "
            "prior appearances toward the positional baseline."
        )
        print("Similarity scores are ranking measures, not probabilities.")

        return results[:limit]

    finally:
        connection.close()


if __name__ == "__main__":
    name = input("Enter a player name: ").strip()
    players = find_similar_players(name)

    if not players:
        print("No similar players found.")
    else:
        print(f"\nPlayers similar to {name}:\n")

        for i, player in enumerate(players, start=1):
            print(
                f"{i}. {player['name']} "
                f"| Position: {player['position']} "
                f"| Apps: {player['appearances']:g} "
                f"| Goals: {player['goals']:g} "
                f"| Assists: {player['assists']:g} "
                f"| Goals/App: {player['goals_per_app']:.3f} "
                f"| Assists/App: {player['assists_per_app']:.3f} "
                f"| Adjusted Goals/App: "
                f"{player['adjusted_goals_per_app']:.3f} "
                f"| Adjusted Assists/App: "
                f"{player['adjusted_assists_per_app']:.3f} "
                f"| Similarity: {player['similarity']:.3f}"
            )