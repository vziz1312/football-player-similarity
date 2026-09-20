import requests
import math
import os
import json
import unicodedata
from dotenv import load_dotenv

load_dotenv()
API_KEY=os.getenv("API_KEY")

url = "https://v3.football.api-sports.io/players"

headers = {
    "x-apisports-key": API_KEY
}

def normalize_name(name):
    name=name.lower()
    name=unicodedata.normalize("NFD", name)
    name="".join(
        char for char in name if unicodedata.category(char) != "Mn"
    )
    return name

def get_player_profile(player_name):

    players = load_player_profiles()
    search_name = normalize_name(player_name)

    for saved_player in players:
        saved_name = normalize_name(saved_player["name"])

        if search_name in saved_name:
            print(
                "Player found in local storage:",
                saved_player["name"]
            )
            return saved_player

    params = {
        "search": player_name,
        "league": 140,
        "season": 2023
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
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

    print(
        player_name,
        "→ results:",
        len(data["response"])
    )

    if not data["response"]:
        print("Player not found.")
        return None

    player = None
    stats = None

    search_name = normalize_name(player_name)

    for result in data["response"]:

        candidate = result["player"]
        candidate_name = normalize_name(candidate["name"])

        if search_name in candidate_name:
            if not result["statistics"]:
                continue
            candidate_stats = result["statistics"][0]
            if not candidate_stats["games"]["minutes"]:
                continue
            player = candidate
            stats = candidate_stats
            break

    if player is None:
        print("Exact player match not found.")
        return None

    minutes = stats["games"]["minutes"]

    if not minutes:
        print("Player has no minutes.")
        return None

    player_profile = {

        "id": player["id"],

        "name": player["name"],

        "position": stats["games"]["position"],

        "minutes": minutes,

        "rating": float(stats["games"]["rating"]),

        "goals": stats["goals"]["total"],

        "assists": stats["goals"]["assists"],

        "shots": stats["shots"]["total"],

        "passes": stats["passes"]["total"],

        "key_passes": stats["passes"]["key"],

        "dribbles": stats["dribbles"]["attempts"],

        "duels": stats["duels"]["total"],

        "duels_won": stats["duels"]["won"],

        "fouls_drawn": stats["fouls"]["drawn"]
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

    save_player_profile(player_profile)

    return player_profile

def save_player_profile(profile):
    with open("players.json", "r") as file:
        players=json.load(file)
    players.append(profile)

    with open("players.json", "w") as file:
        json.dump(players, file, indent=4)

def load_player_profiles():
    with open("players.json", "r") as file:
        players=json.load(file)
    return players

   

def cosine_similarity(vector1, vector2):

    dot_product = 0

    magnitude1 = 0

    magnitude2 = 0

    for i in range(len(vector1)):

        dot_product += (
            vector1[i] * vector2[i]
        )

        magnitude1 += (
            vector1[i] ** 2
        )

        magnitude2 += (
            vector2[i] ** 2
        )

    magnitude1 = math.sqrt(magnitude1)

    magnitude2 = math.sqrt(magnitude2)

    if magnitude1 == 0 or magnitude2 == 0:

        return 0

    return dot_product / (
        magnitude1 * magnitude2
    )



player_pool = [

    "rodrygo",
    "borja mayoral",
    "pedri",
    "ferran torres",
    "joselu",
    "hugo duro",
    "mikel oyarzabal",
    "marcos llorente",

]




pool_profiles = []

for player_name in player_pool:

    profile = get_player_profile(player_name)

    if profile:

        pool_profiles.append(profile)

for profile in pool_profiles:
    print(
        profile["name"],
        "→",profile["position"],
    )
print(
    "Number of profiles:",
    len(pool_profiles)
)

player1_name = input(
    "Enter first player: "
)

player2_name = input(
    "Enter second player: "
)


player1 = get_player_profile(
    player1_name
)

player2 = get_player_profile(
    player2_name
)


if not player1 or not player2:

    print(
        "Could not find one or both players."
    )

    exit()


if not pool_profiles:

    print("No players were found in the pool.")

    exit()


filtered_pool=[]
for profile in pool_profiles:
    if profile["position"] == player1["position"]:
        filtered_pool.append(profile)

features = [

    "goals_per_90",

    "assists_per_90",

    "shots_per_90",

    "passes_per_90",

    "key_passes_per_90",

    "dribbles_per_90",

    "duels_per_90",

    "duels_won_per_90"

]




pool_vectors = []

for profile in filtered_pool:

    vector = []

    for feature in features:

        vector.append(
            profile[feature]
        )

    pool_vectors.append(vector)


normalized_vectors = []

for feature_index in range(
    len(features)
):

    values = []

    for vector in pool_vectors:

        values.append(
            vector[feature_index]
        )

    minimum = min(values)

    maximum = max(values)

    normalized_column = []

    for value in values:

        if maximum == minimum:

            normalized_value = 0

        else:

            normalized_value = (
                value - minimum
            ) / (
                maximum - minimum
            )

        normalized_column.append(
            normalized_value
        )

    normalized_vectors.append(
        normalized_column
    )


normalized_player_vectors = []

for player_index in range(
    len(filtered_pool)
):

    vector = []

    for feature_index in range(
        len(features)
    ):

        vector.append(
            normalized_vectors[
                feature_index
            ][
                player_index
            ]
        )

    normalized_player_vectors.append(
        vector
    )




target_vector = []

for feature_index in range(
    len(features)
):

    values = []

    for vector in pool_vectors:

        values.append(
            vector[feature_index]
        )

    minimum = min(values)

    maximum = max(values)

    value = player1[
        features[feature_index]
    ]

    if maximum == minimum:

        normalized_value = 0

    else:

        normalized_value = (
            value - minimum
        ) / (
            maximum - minimum
        )

    target_vector.append(
        normalized_value
    )



similar_players = []

for i in range(
    len(filtered_pool)
):

    if filtered_pool[i]["name"].lower() == player1["name"].lower():

        continue

    similarity = cosine_similarity(

        target_vector,

        normalized_player_vectors[i]

    )

    similar_players.append(
        (
            filtered_pool[i]["name"],
            similarity
        )
    )


similar_players.sort(
    key=lambda x: x[1],
    reverse=True
)


print(
    "\n===== SIMILAR PLAYERS ====="
)
print(
    "target :",
    player1["name"]

)
print(
    "position :",
    player1["position"]
)

for i,(name, similarity) in enumerate(similar_players[:5], start=1):

    print(
        i,
        ".",
        name,
        ":",
        round(similarity *100, 2),
        "%"
    )

vector1 = []

vector2 = []


for feature in features:

    vector1.append(
        round(
            player1[feature],
            2
        )
    )

    vector2.append(
        round(
            player2[feature],
            2
        )
    )


print(
    "\n===== PLAYER VECTORS ====="
)

print(
    player1["name"],
    ":",
    vector1
)

print(
    player2["name"],
    ":",
    vector2
)


print(
    "\n===== COMPARISON ====="
)

print(
    "Player 1:",
    player1["name"]
)

print(
    "Player 2:",
    player2["name"]
)


print(
    "\nGoals per 90:"
)

print(
    player1["name"],
    ":",
    round(
        player1["goals_per_90"],
        2
    )
)

print(
    player2["name"],
    ":",
    round(
        player2["goals_per_90"],
        2
    )
)


print(
    "\nAssists per 90:"
)

print(
    player1["name"],
    ":",
    round(
        player1["assists_per_90"],
        2
    )
)

print(
    player2["name"],
    ":",
    round(
        player2["assists_per_90"],
        2
    )
)


print(
    "\nShots per 90:"
)

print(
    player1["name"],
    ":",
    round(
        player1["shots_per_90"],
        2
    )
)

print(
    player2["name"],
    ":",
    round(
        player2["shots_per_90"],
        2
    )
)


print(
    "\nDribbles per 90:"
)

print(
    player1["name"],
    ":",
    round(
        player1["dribbles_per_90"],
        2
    )
)

print(
    player2["name"],
    ":",
    round(
        player2["dribbles_per_90"],
        2
    )
)