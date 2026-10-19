
from similarity import cosine_similarity


def test_identical_vectors():
    assert cosine_similarity([1, 0], [1, 0]) == 1.0


def test_perpendicular_vectors():
    assert cosine_similarity([1, 0], [0, 1]) == 0.0


def test_zero_vector():
    assert cosine_similarity([0, 0], [1, 0]) == 0


if __name__ == "__main__":
    test_identical_vectors()
    test_perpendicular_vectors()
    test_zero_vector()
    print("All 3 similarity tests passed!")
