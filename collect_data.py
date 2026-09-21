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
        if players[i]["id"] == profile["id"]:
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
    if not stats["games"]["minutes"]:
        print("No minutes played for", result["player"]["name"])
        return False
    return True

def safe_number(value):

    if value is None:
        return 0

    return value

def transform_player(result):

    player = result["player"]

    if not result["statistics"]:
        print("No statistics available for", player["name"])
        return None

    stats = result["statistics"][0]

    minutes = stats["games"]["minutes"]

    if not minutes:
        print("No minutes played for", player["name"])
        return None

    player_profile = {

        "id": player["id"],
        "name": player["name"],
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

collect_league()