import sqlite3
from pathlib import Path
from math import sqrt
import unicodedata

DB_PATH = Path(__file__).with_name("transfermarkt.db")

RECENT_SEASONS = ("25/26", "24/25", "23/24")
MIN_RECENT_APPEARANCES = 20
MIN_CAREER_APPEARANCES = 100

def normalize_name(value):
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
    """Return player statistics meeting the appearance threshold."""
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


def make_vector(player):
    """Represent a player using goals and assists per appearance."""
    appearances = player["appearances"]

    return [
        player["goals"] / appearances,
        player["assists"] / appearances,
    ]


def calculate_similarity(vector1, vector2):
    """Convert Euclidean distance into a bounded ranking score."""
    distance = sqrt(
        sum((a - b) ** 2 for a, b in zip(vector1, vector2))
    )

    return 1 / (1 + distance)


def find_similar_players(
    player_name,
    limit=10,
    min_recent_appearances=MIN_RECENT_APPEARANCES,
    min_career_appearances=MIN_CAREER_APPEARANCES,
):
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
            connection, target["player_id"], RECENT_SEASONS
        )

        if (
            recent_target is not None
            and recent_target["appearances"] >= min_recent_appearances
        ):
            mode = "recent"
            target_stats = recent_target
            candidate_rows = get_players_stats(
                connection,
                seasons=RECENT_SEASONS,
                min_appearances=min_recent_appearances,
            )
            print("Comparison mode: recent seasons (25/26, 24/25, 23/24)")

        else:
            mode = "career-wide"
            target_stats = get_player_stats(
                connection, target["player_id"]
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
                    "Not enough career appearances for a reliable "
                    "comparison."
                )
                return []

            candidate_rows = get_players_stats(
                connection,
                min_appearances=min_career_appearances,
            )

        target_vector = make_vector(target_stats)
        results = []

        for candidate in candidate_rows:
            if candidate["player_id"] == target["player_id"]:
                continue

            if (
                target_stats["main_position"]
                and candidate["main_position"]
                != target_stats["main_position"]
            ):
                continue

            candidate_vector = make_vector(candidate)

            similarity = calculate_similarity(
                target_vector, candidate_vector
            )

            results.append({
                "name": candidate["player_name"],
                "position": (
                    candidate["main_position"] or candidate["position"]
                ),
                "appearances": candidate["appearances"],
                "goals": candidate["goals"],
                "assists": candidate["assists"],
                "penalty_goals": candidate["penalty_goals"],
                "yellow_cards": candidate["yellow_cards"],
                "goals_per_app": candidate["goals"]
                / candidate["appearances"],
                "assists_per_app": candidate["assists"]
                / candidate["appearances"],
                "similarity": similarity,
            })

        results.sort(
            key=lambda player: player["similarity"],
            reverse=True,
        )

        print(f"Target: {target_stats['player_name']}")
        print(f"Target appearances in comparison period: "
              f"{target_stats['appearances']:g}")
        print(
            "Features used: goals per appearance and "
            "assists per appearance."
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
                f"| Similarity: {player['similarity']:.3f}"
            )