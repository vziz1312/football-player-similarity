import math


def cosine_similarity(vector1, vector2):
    if len(vector1) != len(vector2):
        raise ValueError("Vectors must have the same length.")

    dot_product = 0
    magnitude1 = 0
    magnitude2 = 0

    for i in range(len(vector1)):
        dot_product += vector1[i] * vector2[i]
        magnitude1 += vector1[i] ** 2
        magnitude2 += vector2[i] ** 2

    magnitude1 = math.sqrt(magnitude1)
    magnitude2 = math.sqrt(magnitude2)

    if magnitude1 == 0 or magnitude2 == 0:
        return 0

    return dot_product / (magnitude1 * magnitude2)