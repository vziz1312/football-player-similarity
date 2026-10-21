
import sqlite3
from pathlib import Path
from math import sqrt

DB_PATH = Path(__file__).with_name("transfermarkt.db")


def find_similar_players(player_name, limit=10, min_appearances=100):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        target = connection.execute(
            """
            SELECT player_id, player_name, main_position, position
            FROM players
            WHERE LOWER(TRIM(player_name)) = LOWER(TRIM(?))
               OR LOWER(TRIM(player_name)) LIKE LOWER(TRIM(?))
            ORDER BY
                CASE WHEN LOWER(TRIM(player_name)) = LOWER(TRIM(?))
                     THEN 0 ELSE 1 END
            LIMIT 1
            """,
            (
                player_name.strip(),
                f"{player_name.strip()} (%)",
                player_name.strip(),
            ),
        ).fetchone()

        if target is None:
            print(f"Player not found: {player_name}")
            return []

        rows = connection.execute(
            """
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
            GROUP BY
                p.player_id,
                p.player_name,
                p.main_position,
                p.position
            HAVING SUM(COALESCE(s.nb_on_pitch, 0)) >= ?
            """,
            (min_appearances,),
        ).fetchall()

        target_stats = next(
            (r for r in rows if r["player_id"] == target["player_id"]),
            None,
        )

        if target_stats is None:
            print("Not enough recorded appearances for this player.")
            return []

        def make_vector(row):
            appearances = row["appearances"]
            return [
                row["goals"] / appearances,
                row["assists"] / appearances,
                row["penalty_goals"] / appearances,
                row["yellow_cards"] / appearances,
            ]

        target_vector = make_vector(target_stats)
        results = []

        for row in rows:
            if row["player_id"] == target["player_id"]:
                continue

            if (
                target["main_position"]
                and row["main_position"] != target["main_position"]
            ):
                continue

            candidate_vector = make_vector(row)

            distance = sqrt(
                sum(
                    (a - b) ** 2
                    for a, b in zip(target_vector, candidate_vector)
                )
            )

            score = 1 / (1 + distance)

            results.append({
                "name": row["player_name"],
                "position": row["main_position"] or row["position"],
                "appearances": row["appearances"],
                "goals": row["goals"],
                "assists": row["assists"],
                "penalty_goals": row["penalty_goals"],
                "yellow_cards": row["yellow_cards"],
                "similarity": score,
            })

        results.sort(
            key=lambda player: player["similarity"],
            reverse=True,
        )
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

        for i, p in enumerate(players, start=1):
            print(
                f"{i}. {p['name']} "
                f"| Position: {p['position']} "
                f"| Apps: {p['appearances']:g} "
                f"| Goals: {p['goals']:g} "
                f"| Assists: {p['assists']:g} "
                f"| Penalties: {p['penalty_goals']:g} "
                f"| Yellow cards: {p['yellow_cards']:g} "
                f"| Similarity: {p['similarity']:.3f}"
            )
