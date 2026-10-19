import math
import database


def get_player_profile(player_name):
    profile = database.find_player_profile(player_name)
    if profile:
        print("Player found in SQLite:", profile["name"])
    else:
        print("Player not found or name is ambiguous in the SQLite dataset.")
    return profile



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
    "witsel",
    "oblak",
    "gimenez",
    "griezmann",
    "morata",
    "lewandowski",
    "de jong",
    "gundogan",
]




all_profiles = database.get_player_profiles()
profiles_by_name = {
    profile["name"].casefold(): profile for profile in all_profiles
}
pool_profiles = []

for player_name in player_pool:

    profile = next(
        (item for name, item in profiles_by_name.items() if player_name in name),
        None,
    )

    if profile:

        pool_profiles.append(profile)

for profile in pool_profiles:
    print(
        profile["name"],
        "->", profile["position"],
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

player1_index = next(
    (
        index
        for index, profile in enumerate(filtered_pool)
        if profile["name"].casefold() == player1["name"].casefold()
    ),
    None,
)

if player1_index is None:
    print("Target player is missing from the filtered pool.")
    exit()

for i in range(len(filtered_pool)):
    if i == player1_index:
        continue

    similarity = cosine_similarity(
        pool_vectors[player1_index],
        pool_vectors[i],
    )

    similar_players.append(
        (filtered_pool[i]["name"], similarity)
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
