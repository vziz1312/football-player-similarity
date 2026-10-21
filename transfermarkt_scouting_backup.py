
from multiprocessing.dummy import connection
import sqlite3
from pathlib import Path

from similarity import cosine_similarity

# Use the database in the same folder as this script.
DB_PATH = Path(__file__).with_name("transfermarkt.db")


def find_similar_players(player_name, limit=10, min_minutes=450):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        # Find the requested player.
    
        target = connection.execute(
    """
    SELECT player_id, player_name, main_position, position
    FROM players
    WHERE LOWER(TRIM(player_name)) = LOWER(TRIM(?))
    OR LOWER(TRIM(player_name)) LIKE LOWER(TRIM(?))
    ORDER BY
        CASE
            WHEN LOWER(TRIM(player_name)) = LOWER(TRIM(?)) THEN 0
            ELSE 1
        END
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

        # Aggregate each player's historical performance records.
        rows = connection.execute(
            """
            SELECT
                p.player_id,
                p.player_name,
                p.main_position,
                p.position,
                SUM(COALESCE(s.minutes_played, 0)) AS minutes,
                SUM(COALESCE(s.goals, 0)) AS goals,
                SUM(COALESCE(s.assists, 0)) AS assists
            FROM players AS p
            JOIN performances AS s
                ON s.player_id = p.player_id
            GROUP BY
                p.player_id,
                p.player_name,
                p.main_position,
                p.position
            HAVING SUM(COALESCE(s.minutes_played, 0)) >= ?
            """,
            (min_minutes,),
        ).fetchall()

        # Find the target player's aggregated statistics.
        target_stats = next(
            (row for row in rows if row["player_id"] == target["player_id"]),
            None,
        )

        if target_stats is None:
            print("Not enough recorded minutes for this player.")
            return []

        def make_vector(row):
            minutes = row["minutes"]
            return [
                row["goals"] * 90 / minutes,
                row["assists"] * 90 / minutes,
            ]

        target_vector = make_vector(target_stats)
        results = []

        for row in rows:
            if row["player_id"] == target["player_id"]:
                continue

            # Compare players in the same recorded main position.
            if (
                target["main_position"]
                and row["main_position"] != target["main_position"]
            ):
                continue

            candidate_vector = make_vector(row)

            score = 1 / (
                1 + sum(
        (target_vector[i] - candidate_vector[i]) ** 2
        for i in range(len(target_vector))
    ) ** 0.5
)
            
            results.append({
                "name": row["player_name"],
                "position": row["main_position"] or row["position"],
                "minutes": row["minutes"],
                "goals": row["goals"],
                "assists": row["assists"],
                "similarity": score,
            })

        results.sort(key=lambda player: player["similarity"], reverse=True)
        return results[:limit]

    finally:
        connection.close()


if __name__ == "__main__":
    name = input("Enter a player name: ").strip()

    similar_players = find_similar_players(name)

    if similar_players:
        print(f"\nPlayers similar to {name}:\n")

        for index, player in enumerate(similar_players, start=1):
            print(
                f"{index}. {player['name']} "
                f"| Position: {player['position']} "
                f"| Goals: {player['goals']:g} "
                f"| Assists: {player['assists']:g} "
                f"| Minutes: {player['minutes']:g} "
                f"| Similarity: {player['similarity']:.3f}"
            )
