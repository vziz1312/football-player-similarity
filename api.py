import re
import sqlite3
import unicodedata
from pathlib import Path
from transfermarkt_scouting import find_similar_players

from fastapi import FastAPI, Query, HTTPException


DB_PATH = Path(__file__).with_name("transfermarkt.db")

app = FastAPI(
    title="Football Player Scouting API",
    description="An API for scouting football players based on their performance statistics.",
    version="0.1.0",
)


def normalize_player_name(name: str) -> str:
    """Normalize names so accents and numeric ID suffixes do not matter."""
    name = re.sub(r"\s+\(\d+\)$", "", name.strip())
    name = unicodedata.normalize("NFKD", name).casefold()

    return "".join(
        char for char in name
        if not unicodedata.combining(char)
    )


@app.get("/")
def home():
    return {
        "message": "Welcome to the Football Player Scouting API!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/players/search")
def search_players(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=10, ge=1, le=50),
):
    search_term = normalize_player_name(q)

    if not search_term:
        raise HTTPException(
            status_code=400,
            detail="Please provide a player name.",
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.create_function(
        "normalize_player_name",
        1,
        normalize_player_name,
    )

    try:
        rows = connection.execute(
            """
            SELECT
                player_id,
                player_name,
                date_of_birth,
                height,
                citizenship,
                position,
                main_position,
                foot,
                current_club_name
            FROM players
            WHERE player_name IS NOT NULL
            AND TRIM(player_name) <> ''
            AND instr(
                    normalize_player_name(player_name),
                    ?
            ) > 0
            ORDER BY
                CASE
                    WHEN normalize_player_name(player_name) = ?
                    THEN 0
                    ELSE 1
                END,
                player_name COLLATE NOCASE
            LIMIT ?
            """,
            (search_term, search_term, limit),
        ).fetchall()

    finally:
        connection.close()

    return {
        "query": q,
        "count": len(rows),
        "results": [dict(row) for row in rows],
    }
@app.get("/players/{player_id}/similar")
def get_similar_players(
    player_id: int,
    limit: int = Query(default=10, ge=1, le=50),
):
    connection = sqlite3.connect(DB_PATH)
    try:
        player = connection.execute(
            """
            SELECT player_name
            FROM players
            WHERE player_id = ?
            """,
            (player_id,),
        ).fetchone()
    finally:
        connection.close()
    if player is None or not player[0]:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )
    results = find_similar_players(
        player[0],
        limit=limit,
    )
    return {
        "player_id": player_id,
        "player_name": player[0],
        "count": len(results),
        "results": results,
    }
