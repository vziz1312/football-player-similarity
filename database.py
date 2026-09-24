import sqlite3
import json


def load_players():
    with open("players.json", "r", encoding="utf-8") as file:
        return json.load(file)


def create_players_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            team_id INTEGER,
            team_name TEXT,
            position TEXT,
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
            fouls_drawn REAL
        )
    """)


def insert_player(cursor, player):
    cursor.execute("""
        INSERT OR REPLACE INTO players (
            id,
            name,
            team_id,
            team_name,
            position,
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        player["id"],
        player["name"],
        player["team_id"],
        player["team_name"],
        player["position"],
        player["minutes"],
        player["rating"],
        player["goals"],
        player["assists"],
        player["shots"],
        player["passes"],
        player["key_passes"],
        player["dribbles"],
        player["duels"],
        player["duels_won"],
        player["fouls_drawn"]
    ))

def migrate_players(cursor, players):
    for player in players:
        insert_player(cursor, player)


def main():
    connection = sqlite3.connect("football.db")
    print("Database connected successfully")

    cursor = connection.cursor()

    create_players_table(cursor)

    players = load_players()
    print("Players loaded from JSON:", len(players))

    migrate_players(cursor, players)

    connection.commit()

    print("Players inserted successfully:", len(players))

    connection.close()


if __name__ == "__main__":
    main()