
import sqlite3
from pathlib import Path

import pandas as pd

# Transfermarkt CSV locations
DATA_DIR = Path(
    r"C:\Users\aziz\Downloads\football-datasets-main"
    r"\football-datasets-main\datalake\transfermarkt"
)

PROFILES_CSV = DATA_DIR / "player_profiles" / "player_profiles.csv"

PERFORMANCES_CSV = (
    DATA_DIR
    / "player_performances"
    / "football-datasets"
    / "datalake"
    / "transfermarkt"
    / "player_performances"
    / "player_performances.csv"
)

# A separate database: football.db will not be modified.
DB_PATH = Path(__file__).resolve().parent / "transfermarkt.db"


def main():
    if not PROFILES_CSV.exists():
        raise FileNotFoundError(f"Profiles CSV not found: {PROFILES_CSV}")

    if not PERFORMANCES_CSV.exists():
        raise FileNotFoundError(
            f"Performances CSV not found: {PERFORMANCES_CSV}"
        )

    print("Connecting to the new database...")
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("PRAGMA journal_mode=WAL")

        connection.executescript("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY,
                player_name TEXT,
                position TEXT,
                main_position TEXT,
                citizenship TEXT,
                date_of_birth TEXT,
                height REAL,
                foot TEXT,
                current_club_name TEXT
            );

            CREATE TABLE IF NOT EXISTS performances (
                player_id INTEGER NOT NULL,
                season_name TEXT,
                competition_id TEXT,
                competition_name TEXT,
                team_id INTEGER,
                team_name TEXT,
                goals REAL,
                assists REAL,
                minutes_played REAL,
                yellow_cards REAL,
                second_yellow_cards REAL,
                direct_red_cards REAL,
                penalty_goals REAL,
                goals_conceded REAL,
                clean_sheets REAL
            );

            CREATE INDEX IF NOT EXISTS idx_performances_player
            ON performances(player_id);

            CREATE INDEX IF NOT EXISTS idx_performances_season
            ON performances(season_name);

            CREATE INDEX IF NOT EXISTS idx_performances_competition
            ON performances(competition_id);
        """)

        print("Importing player profiles...")
        profiles = pd.read_csv(
            PROFILES_CSV,
            usecols=[
                "player_id",
                "player_name",
                "position",
                "main_position",
                "citizenship",
                "date_of_birth",
                "height",
                "foot",
                "current_club_name",
            ],
        )

        profiles = profiles.drop_duplicates(
            subset=["player_id"], keep="last"
        )

        profiles.to_sql(
            "players",
            connection,
            if_exists="replace",
            index=False,
            chunksize=5000,
        )

        # Recreate the index after replacing the table.
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_performances_player
            ON performances(player_id)
        """)

        print(f"Imported {len(profiles):,} player profiles.")
        del profiles

        print("Importing performance records...")
        columns = [
            "player_id",
            "season_name",
            "competition_id",
            "competition_name",
            "team_id",
            "team_name",
            "goals",
            "assists",
            "minutes_played",
            "yellow_cards",
            "second_yellow_cards",
            "direct_red_cards",
            "penalty_goals",
            "goals_conceded",
            "clean_sheets",
        ]

        total = 0

        for chunk in pd.read_csv(
            PERFORMANCES_CSV,
            usecols=columns,
            chunksize=50000,
        ):
            chunk.to_sql(
                "performances",
                connection,
                if_exists="append",
                index=False,
                chunksize=5000,
            )

            total += len(chunk)
            print(f"Imported {total:,} performance records...")

        connection.commit()

        player_count = connection.execute(
            "SELECT COUNT(*) FROM players"
        ).fetchone()[0]

        performance_count = connection.execute(
            "SELECT COUNT(*) FROM performances"
        ).fetchone()[0]

        print("\nImport complete!")
        print(f"Database: {DB_PATH}")
        print(f"Players: {player_count:,}")
        print(f"Performance records: {performance_count:,}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
