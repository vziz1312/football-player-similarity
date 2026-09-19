import requests
import math
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY=os.getenv("API_KEY")

url = "https://v3.football.api-sports.io/players"

headers = {
    "x-apisports-key": API_KEY
}


def get_player_profile(player_name):

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

    # Check API errors first
    if data["errors"]:
        print("API Error:", data["errors"])
        return None

    print(
        player_name,
        "→ results:",
        len(data["response"])
    )

    # Player doesn't exist / wasn't found
    if not data["response"]:
        print("Player not found.")
        return None

    player = data["response"][0]["player"]

    stats = data["response"][0]["statistics"][0]

    minutes = stats["games"]["minutes"]

    if not minutes:
        print("Player has no minutes.")
        return None


    player_profile = {

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


    # ==========================================
    # PER 90 STATISTICS
    # ==========================================

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

    "rodrygo"

]




pool_profiles = []

for player_name in player_pool:

    profile = get_player_profile(player_name)

    if profile:

        pool_profiles.append(profile)


print(
    "Number of profiles:",
    len(pool_profiles)
)




if not pool_profiles:

    print("No players were found in the pool.")

    exit()



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

for profile in pool_profiles:

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
    len(pool_profiles)
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



similarities = []

for i in range(
    len(pool_profiles)
):

    similarity = cosine_similarity(

        target_vector,

        normalized_player_vectors[i]

    )

    similarities.append(
        similarity
    )



print(
    "\n===== SIMILARITY TEST ====="
)

for i in range(
    len(pool_profiles)
):

    print(

        pool_profiles[i]["name"],

        ":",

        round(
            similarities[i],
            3
        )

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