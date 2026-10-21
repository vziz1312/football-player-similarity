
import sqlite3
from pathlib import Path
from math import sqrt

DB_PATH = Path(__file__).with_name("transfermarkt.db")

RECENT_SEASONS = ("25/26", "24/25", "23/24")
MIN_APPEARANCES = 20


def find_similar_players(player_name, limit=10):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        target = connection.execute(
            """
            SELECT player_id, player_name, main_position, position,
                   height, foot
            FROM players
            WHERE LOWER(TRIM(player_name)) = LOWER(TRIM(?))
               OR LOWER(TRIM(player_name)) LIKE LOWER(TRIM(?))
            ORDER BY CASE
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
            print(f"Player not found: {player_name}")
            return []

        if not target["main_position"]:
            print("The selected player has no recorded main position.")
            return []

        placeholders = ",".join("?" for _ in RECENT_SEASONS)

        query = f"""
            SELECT
                p.player_id,
                p.player_name,
                p.main_position,
                p.position,
                p.height,
                p.foot,
                SUM(COALESCE(s.nb_on_pitch, 0)) AS appearances,
                SUM(COALESCE(s.goals, 0)) AS goals,
                SUM(COALESCE(s.assists, 0)) AS assists,
                SUM(COALESCE(s.penalty_goals, 0)) AS penalty_goals
            FROM players p
            JOIN performances s ON s.player_id = p.player_id
            WHERE s.season_name IN ({placeholders})
              AND p.main_position = ?
            GROUP BY
                p.player_id, p.player_name, p.main_position,
                p.position, p.height, p.foot
            HAVING SUM(COALESCE(s.nb_on_pitch, 0)) >= ?
        """

        rows = connection.execute(
            query,
            (*RECENT_SEASONS, target["main_position"], MIN_APPEARANCES),
        ).fetchall()

        target_stats = connection.execute(
            f"""
            SELECT
                SUM(COALESCE(s.nb_on_pitch, 0)) AS appearances,
                SUM(COALESCE(s.goals, 0)) AS goals,
                SUM(COALESCE(s.assists, 0)) AS assists,
                SUM(COALESCE(s.penalty_goals, 0)) AS penalty_goals
            FROM performances s
            WHERE s.player_id = ?
              AND s.season_name IN ({placeholders})
            """,
            (target["player_id"], *RECENT_SEASONS),
        ).fetchone()

        if not target_stats or not target_stats["appearances"]:
            print("No usable records for this player in the selected seasons.")
            return []

        target_apps = target_stats["appearances"]

        if target_apps < MIN_APPEARANCES:
            print(
                f"WARNING: Only {target_apps:g} recorded appearances "
                "for the target. Rankings may be unreliable."
            )

        def rates(row):
            apps = row["appearances"]
            goals = row["goals"]
            assists = row["assists"]
            penalties = row["penalty_goals"]

            return [
                goals / apps,
                assists / apps,
                max(0, goals - penalties) / apps,
                penalties / apps,
            ]

        target_vector = rates(target_stats)
        results = []

        for row in rows:
            if row["player_id"] == target["player_id"]:
                continue

            candidate_vector = rates(row)

            # Equal weighting for the four rate features.
            performance_distance = sqrt(
                sum(
                    (a - b) ** 2
                    for a, b in zip(target_vector, candidate_vector)
                ) / len(target_vector)
            )

            # Optional profile differences.
            profile_penalty = 0.0

            if target["height"] is not None and row["height"] is not None:
                profile_penalty += min(
                    abs(target["height"] - row["height"]) / 20, 1
                ) * 0.10

            if target["foot"] and row["foot"]:
                if target["foot"].lower() != row["foot"].lower():
                    profile_penalty += 0.05

            distance = performance_distance + profile_penalty
            similarity = 1 / (1 + distance)

            results.append({
                "name": row["player_name"],
                "position": row["main_position"],
                "appearances": row["appearances"],
                "goals": row["goals"],
                "assists": row["assists"],
                "penalty_goals": row["penalty_goals"],
                "height": row["height"],
                "foot": row["foot"],
                "similarity": similarity,
                "target_appearances": target_apps,
                "candidate_confidence": (
                    "Low" if row["appearances"] < 30
                    else "Better sample"
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
        print(f"\nSimilar recent player profiles for {name}:\n")

        for i, player in enumerate(players, start=1):
            print(
                f"{i}. {player['name']} "
                f"| Position: {player['position']} "
                f"| Apps: {player['appearances']:g} "
                f"| Goals: {player['goals']:g} "
                f"| Assists: {player['assists']:g} "
                f"| Penalties: {player['penalty_goals']:g} "
                f"| Height: {player['height']} "
                f"| Foot: {player['foot']} "
                f"| Similarity: {player['similarity']:.3f} "
                f"| Target Apps: {player['target_appearances']:g} "
                f"| Candidate Sample: {player['candidate_confidence']}"
            )
    else:
        print("No similar players found.")
