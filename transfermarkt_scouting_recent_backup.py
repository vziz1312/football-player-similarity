
import sqlite3
from pathlib import Path
from math import sqrt

DB_PATH = Path(__file__).with_name("transfermarkt.db")

# Three most recent seasons represented in our database.
RECENT_SEASONS = ("25/26", "24/25", "23/24")

MIN_APPEARANCES = 20


def find_similar_players(player_name, limit=10):
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
                CASE
                    WHEN LOWER(TRIM(player_name)) = LOWER(TRIM(?))
                    THEN 0 ELSE 1
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
            print(f"Exact player name not found: {player_name}")
            return []

        if not target["main_position"]:
            print("The selected player has no recorded main position.")
            return []

        placeholders = ",".join("?" for _ in RECENT_SEASONS)

        rows = connection.execute(
            f"""
            SELECT
                p.player_id,
                p.player_name,
                p.main_position,
                p.position,
                SUM(COALESCE(s.nb_on_pitch, 0)) AS appearances,
                SUM(COALESCE(s.goals, 0)) AS goals,
                SUM(COALESCE(s.assists, 0)) AS assists
            FROM players p
            JOIN performances s ON s.player_id = p.player_id
            WHERE s.season_name IN ({placeholders})
              AND p.main_position = ?
            GROUP BY
                p.player_id,
                p.player_name,
                p.main_position,
                p.position
            HAVING SUM(COALESCE(s.nb_on_pitch, 0)) >= ?
            """,
            (*RECENT_SEASONS, target["main_position"], MIN_APPEARANCES),
        ).fetchall()

        
        target_stats = connection.execute(
            f"""
            SELECT
                p.player_id,
                p.player_name,
                p.main_position,
                SUM(COALESCE(s.nb_on_pitch, 0)) AS appearances,
                SUM(COALESCE(s.goals, 0)) AS goals,
                SUM(COALESCE(s.assists, 0)) AS assists
            FROM players p
            JOIN performances s ON s.player_id = p.player_id
            WHERE p.player_id = ?
            AND s.season_name IN ({placeholders})
            GROUP BY p.player_id, p.player_name, p.main_position
            """,
            (target["player_id"], *RECENT_SEASONS),
        ).fetchone()

        if target_stats is None or target_stats["appearances"] <= 0:
            print("No usable records for this player in the selected seasons.")
            return []

        if target_stats["appearances"] < MIN_APPEARANCES:
            print(
                f"WARNING: Only {target_stats['appearances']:g} recorded "
                "appearances for the target. Treat rankings as low-confidence."
            )

        def make_vector(row):
            apps = row["appearances"]
            return [row["goals"] / apps, row["assists"] / apps]

        target_vector = make_vector(target_stats)
        results = []

        for row in rows:
            if row["player_id"] == target["player_id"]:
                continue

            candidate_vector = make_vector(row)

            distance = sqrt(
                sum(
                    (a - b) ** 2
                    for a, b in zip(target_vector, candidate_vector)
                )
            )

            results.append({
                "name": row["player_name"],
                "position": row["main_position"],
                "appearances": row["appearances"],
                "goals": row["goals"],
                "assists": row["assists"],
                "similarity": 1 / (1 + distance),
                "target_appearances": target_stats["appearances"],
"candidate_confidence": (
    "Low" if row["appearances"] < 30 else "Better sample"
),
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

    if players:
        print(f"\nPlayers with similar recent attacking output to {name}:\n")

        for i, player in enumerate(players, start=1):
            print(
                f"{i}. {player['name']} "
                f"| Position: {player['position']} "
                f"| Apps: {player['appearances']:g} "
                f"| Goals: {player['goals']:g} "
                f"| Assists: {player['assists']:g} "
                f"| Similarity: {player['similarity']:.3f} "
f"| Target Apps: {player['target_appearances']:g} "
f"| Candidate Sample: {player['candidate_confidence']}"
            )
    else:
        print("No similar players found.")
