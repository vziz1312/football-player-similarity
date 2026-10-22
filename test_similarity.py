from similarity import cosine_similarity


def test_identical_vectors():
    assert cosine_similarity([1, 0], [1, 0]) == 1.0


def test_perpendicular_vectors():
    assert cosine_similarity([1, 0], [0, 1]) == 0.0


def test_opposite_vectors():
    assert cosine_similarity([1, 0], [-1, 0]) == -1.0


def test_zero_vector():
    assert cosine_similarity([0, 0], [1, 0]) == 0.0


def test_scaled_vectors():
    assert abs(cosine_similarity([1, 2], [2, 4]) - 1.0) < 1e-9


def test_mismatched_vectors():
    try:
        cosine_similarity([1, 2], [1])
    except ValueError:
        return

    raise AssertionError("Expected ValueError for vectors of different lengths.")


if __name__ == "__main__":
    test_identical_vectors()
    test_perpendicular_vectors()
    test_opposite_vectors()
    test_zero_vector()
    test_scaled_vectors()
    test_mismatched_vectors()
    print("All 6 similarity tests passed!")