import sqlite3


def create_players_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            position TEXT
        )
    """)


def create_teams_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)


def create_leagues_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leagues (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)


def create_seasons_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seasons (
            id INTEGER PRIMARY KEY,
            year INTEGER NOT NULL
        )
    """)


def create_player_stats_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            team_id INTEGER,
            league_id INTEGER NOT NULL,
            season_id INTEGER NOT NULL,
            minutes INTEGER,
            rating REAL,
            goals REAL,
            assists REAL,
            shots REAL,
            passes REAL,
            key_passes REAL,
            dribbles REAL,
            duels REAL,
            duels_won REAL,
            fouls_drawn REAL,

            UNIQUE(player_id, team_id, league_id, season_id),

            FOREIGN KEY (player_id) REFERENCES players(id),
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (league_id) REFERENCES leagues(id),
            FOREIGN KEY (season_id) REFERENCES seasons(id)
        )
    """)


def insert_league(cursor, league_id, league_name):
    cursor.execute("""
        INSERT OR IGNORE INTO leagues (id, name)
        VALUES (?, ?)
    """, (league_id, league_name))


def insert_season(cursor, season_id, year):
    cursor.execute("""
        INSERT OR IGNORE INTO seasons (id, year)
        VALUES (?, ?)
    """, (season_id, year))


def main():
    connection = sqlite3.connect("football.db")

    print("Database connected successfully")

    cursor = connection.cursor()

    create_players_table(cursor)
    create_teams_table(cursor)
    create_leagues_table(cursor)
    create_seasons_table(cursor)
    create_player_stats_table(cursor)

    insert_league(cursor, 140, "La Liga")
    insert_season(cursor, 2023, 2023)

    connection.commit()

    print("Database structure verified successfully")

    connection.close()


if __name__ == "__main__":
    main()