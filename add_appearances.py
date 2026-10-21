
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

CSV_PATH = Path(
    r"C:\Users\aziz\Downloads\football-datasets-main"
    r"\football-datasets-main\datalake\transfermarkt"
    r"\player_performances\football-datasets\datalake"
    r"\transfermarkt\player_performances\player_performances.csv"
)

DB_PATH = BASE_DIR / "transfermarkt.db"


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    connection = sqlite3.connect(DB_PATH)

    try:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(performances)"
            )
        }

        if "nb_on_pitch" not in columns:
            connection.execute(
                "ALTER TABLE performances ADD COLUMN nb_on_pitch INTEGER"
            )

        connection.execute("DROP TABLE IF EXISTS temp_appearances")

        connection.execute("""
            CREATE TEMP TABLE temp_appearances (
                player_id INTEGER,
                season_name TEXT,
                competition_id TEXT,
                team_id INTEGER,
                nb_on_pitch INTEGER
            )
        """)

        print("Reading CSV and loading temporary table...")

        selected = [
            "player_id",
            "season_name",
            "competition_id",
            "team_id",
            "nb_on_pitch",
        ]

        total = 0

        for chunk in pd.read_csv(
            CSV_PATH,
            usecols=selected,
            chunksize=50000,
        ):
            chunk = chunk.drop_duplicates(
                subset=[
                    "player_id",
                    "season_name",
                    "competition_id",
                    "team_id",
                ],
                keep="last",
            )

            records = []
            for row in chunk.itertuples(index=False, name=None):
                player_id, season, competition, team, appearances = row

                records.append((
                    int(player_id),
                    str(season),
                    str(competition),
                    None if pd.isna(team) else int(team),
                    None if pd.isna(appearances) else int(appearances),
                ))

            connection.executemany("""
                INSERT INTO temp_appearances
                VALUES (?, ?, ?, ?, ?)
            """, records)

            total += len(records)
            print(f"Loaded {total:,} CSV rows...")

        print("Indexing temporary data...")

        connection.execute("""
            CREATE INDEX idx_temp_appearances_match
            ON temp_appearances (
                player_id, season_name, competition_id, team_id
            )
        """)

        print("Updating database in bulk...")

        connection.execute("""
            UPDATE performances
            SET nb_on_pitch = (
                SELECT a.nb_on_pitch
                FROM temp_appearances AS a
                WHERE a.player_id = performances.player_id
                  AND a.season_name IS performances.season_name
                  AND a.competition_id IS performances.competition_id
                  AND a.team_id IS performances.team_id
            )
            WHERE EXISTS (
                SELECT 1
                FROM temp_appearances AS a
                WHERE a.player_id = performances.player_id
                  AND a.season_name IS performances.season_name
                  AND a.competition_id IS performances.competition_id
                  AND a.team_id IS performances.team_id
            )
        """)

        connection.commit()

        filled = connection.execute("""
            SELECT COUNT(*)
            FROM performances
            WHERE nb_on_pitch IS NOT NULL
        """).fetchone()[0]

        print("\nUpdate complete!")
        print(f"CSV rows loaded: {total:,}")
        print(f"Database rows with appearances: {filled:,}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
