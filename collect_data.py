import requests 
import os
import json 
from dotenv import load_dotenv
import unicodedata


load_dotenv()
API_KEY = os.getenv("API_KEY")

headers = {
    "x-apisports-key": API_KEY
    
}

url = "https://v3.football.api-sports.io/players"
UPDATE_MODE = False

def normalize_name(name):

    name = name.lower()

    name = unicodedata.normalize("NFD", name)

    name = "".join(
        char
        for char in name
        if unicodedata.category(char) != "Mn"
    )

    return name

def save_player_profile(profile):
    try:
        with open("players.json", "r") as file:
            players = json.load(file)
    except FileNotFoundError:
        players = []

    updated = False
    for i in range(len(players)):
        if (players[i]["id"] == profile["id"]) and (players[i].get("team_id") == profile["team_id"]):
            players[i] = profile
            updated = True
            break

    if not updated:
        players.append(profile)

    with open("players.json", "w") as file:
        json.dump(players, file, indent=4)
    if updated:
        print("Player profile updated:", profile["name"])
    else:
        print("Player profile saved:", profile["name"])
        


def validate_player(result):
    if not result["statistics"]:
        print("No statistics available for", result["player"]["name"])
        return False
    stats =result["statistics"][0]
    minutes =stats["games"]["minutes"]
    if not minutes:
        print("No minutes played for", result["player"]["name"])
        return False
    if minutes <450 :
        print("not enough minutes played for", result["player"]["name"])
        return False
    return True

def safe_number(value):

    if value is None:
        return 0

    try:
        return float(value)
    except (ValueError, TypeError):
        return 0

def statistics_signature(stats):
    return (
        stats["games"]["minutes"],
        stats["goals"]["total"],
        stats["goals"]["assists"],
        stats["shots"]["total"],
        stats["passes"]["total"],
        stats["passes"]["key"],
        stats["dribbles"]["attempts"],
        stats["duels"]["total"],
        stats["duels"]["won"]
    )

def get_team_statistics(result):

    statistics = result["statistics"]

    if not statistics:
        print("No statistics available for", result["player"]["name"])
        return None

    unique_statistics = []
    seen_signatures = set()

    for stats in statistics:

        signature = statistics_signature(stats)

        if signature in seen_signatures:
            print(
                "Duplicate statistics detected for:",
                result["player"]["name"],
                "| Team:",
                stats["team"]["name"]
            )
            continue

        seen_signatures.add(signature)
        unique_statistics.append(stats)

    if not unique_statistics:
        return None

    if len(unique_statistics) == 1:
        return unique_statistics[0]

    print()
    print(
        "Multiple unique team statistics found for:",
        result["player"]["name"]
    )

    total_minutes = 0
    total_goals = 0
    total_assists = 0
    total_shots = 0
    total_rating = 0
    total_passes = 0
    total_key_passes = 0
    total_dribbles = 0
    total_duels = 0
    total_duels_won = 0
    total_fouls_drawn = 0

    for stats in unique_statistics:

        print(
            "Aggregating:",
            stats["team"]["name"]
        )

        total_minutes += safe_number(
            stats["games"]["minutes"]
        )

        total_goals += safe_number(
            stats["goals"]["total"]
        )

        total_assists += safe_number(
            stats["goals"]["assists"]
        )

        total_shots += safe_number(
            stats["shots"]["total"]
        )

        total_passes += safe_number(
            stats["passes"]["total"]
        )

        total_key_passes += safe_number(
            stats["passes"]["key"]
        )

        total_dribbles += safe_number(
            stats["dribbles"]["attempts"]
        )

        total_duels += safe_number(
            stats["duels"]["total"]
        )

        total_duels_won += safe_number(
            stats["duels"]["won"]
        )

        total_fouls_drawn += safe_number(
            stats["fouls"]["drawn"]
        )
        
        if stats["games"]["rating"] is not None:
            total_rating += (
                float(stats["games"]["rating"])
                * safe_number(stats["games"]["minutes"])
            )
    average_rating = (
    total_rating / total_minutes
    if total_minutes > 0
    else 0
)

    aggregated_stats = {
        "team": {
            "id": None,
            "name": "Multiple teams"
        },

        "games": {
            "minutes": total_minutes,
            "position": unique_statistics[0]["games"]["position"],
            "rating": average_rating
            
        },

        "goals": {
            "total": total_goals,
            "assists": total_assists
        },

        "shots": {
            "total": total_shots
        },

        "passes": {
            "total": total_passes,
            "key": total_key_passes
        },

        "dribbles": {
            "attempts": total_dribbles
        },

        "duels": {
            "total": total_duels,
            "won": total_duels_won
        },

        "fouls": {
            "drawn": total_fouls_drawn
        }
    }

    return aggregated_stats

def transform_player(result):

    player = result["player"]

    if not result["statistics"]:
        print("No statistics available for", player["name"])
        return None

    stats = get_team_statistics(result)
    if not stats:
        return None
    
    print()
    print("Transforming team:", stats["team"]["name"])
    minutes = stats["games"]["minutes"]

    if not minutes:
        print("No minutes played for", player["name"])
        return None

    player_profile = {

        "id": player["id"],
        "name": player["name"],
        "team_id": stats["team"]["id"],
        "team_name": stats["team"]["name"],
        "position": stats["games"]["position"],
        "minutes": minutes,

        "rating": (
            float(stats["games"]["rating"])
            if stats["games"]["rating"] is not None
            else 0
        ),

        "goals": safe_number(stats["goals"]["total"]),
        "assists": safe_number(stats["goals"]["assists"]),
        "shots": safe_number(stats["shots"]["total"]),
        "passes": safe_number(stats["passes"]["total"]),
        "key_passes": safe_number(stats["passes"]["key"]),
        "dribbles": safe_number(stats["dribbles"]["attempts"]),
        "duels": safe_number(stats["duels"]["total"]),
        "duels_won": safe_number(stats["duels"]["won"]),
        "fouls_drawn": safe_number(stats["fouls"]["drawn"])
    }

    player_profile["goals_per_90"] = (
        player_profile["goals"] / minutes
    ) * 90

    player_profile["assists_per_90"] = (
        player_profile["assists"] / minutes
    ) * 90

    player_profile["shots_per_90"] = (
        player_profile["shots"] / minutes
    ) * 90

    player_profile["passes_per_90"] = (
        player_profile["passes"] / minutes
    ) * 90

    player_profile["key_passes_per_90"] = (
        player_profile["key_passes"] / minutes
    ) * 90

    player_profile["dribbles_per_90"] = (
        player_profile["dribbles"] / minutes
    ) * 90

    player_profile["duels_per_90"] = (
        player_profile["duels"] / minutes
    ) * 90

    player_profile["duels_won_per_90"] = (
        player_profile["duels_won"] / minutes
    ) * 90

    return player_profile


def get_saved_players(player_name):
    try:
        with open("players.json", "r") as file:
            players = json.load(file)
    except FileNotFoundError:
        return None

    search_name = normalize_name(player_name)
    for player in players:
        saved_name = normalize_name(player["name"])
        if search_name in saved_name:
            print("Found saved profile for:", player["name"])
            return player
    return None

def process_player(player_name):

    print()
    print("Processing:", player_name)

    saved_player = get_saved_players(player_name)

    if saved_player and not UPDATE_MODE:
        print("Using saved profile for:", player_name)
        return saved_player

    result = collect_player(player_name)

    if not result:
        return None

    if not validate_player(result):
        return None

    profile = transform_player(result)

    if not profile:
        return None

    save_player_profile(profile)

    return profile

def collect_player(player_name):

    params = {
        "search": player_name,
        "league": 140,
        "season": 2023
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    print(
        "Daily limit:",
        response.headers.get("x-ratelimit-requests-limit")
    )

    print(
        "Remaining today:",
        response.headers.get("x-ratelimit-requests-remaining")
    )

    data = response.json()

    if data["errors"]:
        print("API Error:", data["errors"])
        return None

    if not data["response"]:
        print("Player not found.")
        return None

    print(
        player_name,
        "→ results:",
        len(data["response"])
    )

    search_name = normalize_name(player_name)

    for result in data["response"]:

        candidate = result["player"]

        candidate_name = normalize_name(candidate["name"])

        if search_name in candidate_name:

            print("Selected:", candidate["name"])
            print("number of statistics:", len(result["statistics"]))
            for stats in result["statistics"]:
                print("Team:", stats["team"]["name"])
                print("Minutes:", stats["games"]["minutes"])
                print("Goals:", stats["goals"]["total"])
            return result

    print("Exact player match not found.")

    return None

def collect_league_page(page):

    params = {
        "league": 140,
        "season": 2023,
        "page": page
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    data = response.json()

    if data["errors"]:
        print("API Error:", data["errors"])
        return None

    print()
    print("League page:", page)
    print("Players returned:", len(data["response"]))
    print("Total pages:", data["paging"]["total"])

    return data["response"]

def migrate_players():
    if os.path.exists("players_new.json"):
        print("Migration already completed. File exists: players_new.json")
        return

    migrated_players = []

    for page in range(1, 4):

        print()
        print("==============================")
        print("Migrating page:", page)
        print("==============================")

        players = collect_league_page(page)

        if not players:
            print("No players returned. Stopping.")
            break

        for result in players:

            print()
            print("Processing:", result["player"]["name"])

            if not validate_player(result):
                continue

            profile = transform_player(result)

            if profile:
                migrated_players.append(profile)

    with open("players_new.json", "w") as file:
        json.dump(migrated_players, file, indent=4)

    print()
    print("Migration complete.")
    print("New records:", len(migrated_players))

def collect_league():

    seen_ids = set()

    first_page = collect_league_page(1)

    if not first_page:
        return

    total_pages = 45

    for page in range(1, total_pages + 1):

        print()
        print("==============================")
        print("Collecting page:", page)
        print("==============================")

        if page == 1:
            players = first_page
        else:
            players = collect_league_page(page)

        if not players:
            print("No players returned. Stopping.")
            break

        for result in players:

            player_id = result["player"]["id"]

            if player_id in seen_ids:
                continue

            seen_ids.add(player_id)

            print()
            print("Processing:", result["player"]["name"])

            if not validate_player(result):
                continue

            profile = transform_player(result)

            if profile:
                save_player_profile(profile)

#collect_league()
#migrate_players()
result = collect_player("Witsel")

if result:

    print()
    print("Testing final multi-team handling...")

    profile = transform_player(result)

    if profile:
        print()
        print("FINAL PROFILE")
        print("Name:", profile["name"])
        print("Team:", profile["team_name"])
        print("Minutes:", profile["minutes"])
        print("Goals:", profile["goals"])
        print("Goals per 90:", profile["goals_per_90"])