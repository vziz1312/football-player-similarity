import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("football.db")


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

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


def insert_player(cursor, player_id, name, position):
    cursor.execute("""
        INSERT OR IGNORE INTO players (id, name, position)
        VALUES (?, ?, ?)
    """, (player_id, name, position))


def insert_team(cursor, team_id, team_name):
    cursor.execute("""
        INSERT OR IGNORE INTO teams (id, name)
        VALUES (?, ?)
    """, (team_id, team_name))


def insert_player_stats(cursor, profile, league_id, season_id):
    cursor.execute("""
        INSERT INTO player_stats (
            player_id,
            team_id,
            league_id,
            season_id,
            minutes,
            rating,
            goals,
            assists,
            shots,
            passes,
            key_passes,
            dribbles,
            duels,
            duels_won,
            fouls_drawn
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(player_id, team_id, league_id, season_id)
        DO UPDATE SET
            minutes = excluded.minutes,
            rating = excluded.rating,
            goals = excluded.goals,
            assists = excluded.assists,
            shots = excluded.shots,
            passes = excluded.passes,
            key_passes = excluded.key_passes,
            dribbles = excluded.dribbles,
            duels = excluded.duels,
            duels_won = excluded.duels_won,
            fouls_drawn = excluded.fouls_drawn
    """, (
        profile["id"],
        profile["team_id"],
        league_id,
        season_id,
        profile["minutes"],
        profile["rating"],
        profile["goals"],
        profile["assists"],
        profile["shots"],
        profile["passes"],
        profile["key_passes"],
        profile["dribbles"],
        profile["duels"],
        profile["duels_won"],
        profile["fouls_drawn"]
    ))


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


PER_90_FIELDS = {
    "goals_per_90": "goals",
    "assists_per_90": "assists",
    "shots_per_90": "shots",
    "passes_per_90": "passes",
    "key_passes_per_90": "key_passes",
    "dribbles_per_90": "dribbles",
    "duels_per_90": "duels",
    "duels_won_per_90": "duels_won",
}


def get_player_profiles(league_id=140, season_id=2023):
    """Return player statistics in the profile shape used by the scouting app."""
    query = """
        SELECT p.id, p.name, p.position, t.name AS team_name,
               s.minutes, s.rating, s.goals, s.assists, s.shots,
               s.passes, s.key_passes, s.dribbles, s.duels,
               s.duels_won, s.fouls_drawn
        FROM players AS p
        JOIN player_stats AS s ON s.player_id = p.id
        LEFT JOIN teams AS t ON t.id = s.team_id
        WHERE s.league_id = ? AND s.season_id = ?
        ORDER BY p.name
    """
    with get_connection() as connection:
        rows = connection.execute(query, (league_id, season_id)).fetchall()

    profiles = []
    for row in rows:
        profile = dict(row)
        minutes = profile.get("minutes") or 0
        for per_90_field, raw_field in PER_90_FIELDS.items():
            value = profile.get(raw_field) or 0
            profile[per_90_field] = value * 90 / minutes if minutes else 0
        profiles.append(profile)
    return profiles


def find_player_profile(player_name, league_id=140, season_id=2023):
    """Find a player by exact name first, then by an unambiguous partial name."""
    import unicodedata

    def normalize(value):
        value = unicodedata.normalize("NFD", value.casefold())
        return "".join(char for char in value if unicodedata.category(char) != "Mn")

    query = normalize(player_name.strip())
    if not query:
        return None
    profiles = get_player_profiles(league_id, season_id)
    exact = [profile for profile in profiles if normalize(profile["name"]) == query]
    if exact:
        return exact[0]
    matches = [profile for profile in profiles if query in normalize(profile["name"])]
    return matches[0] if len(matches) == 1 else None


def main():
    connection = get_connection()

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
