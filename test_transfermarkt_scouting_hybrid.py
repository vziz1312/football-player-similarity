from transfermarkt_scouting_hybrid import (
    calculate_similarity,
    normalize_name,
)
from transfermarkt_scouting_hybrid import make_vector


def test_accent_insensitive_matching():
    assert normalize_name("Kylian Mbappé") == normalize_name("kylian mbappe")


def test_uppercase_and_accents():
    assert normalize_name("BÉRGSON") == normalize_name("bergson")


def test_whitespace():
    assert normalize_name("  Lionel Messi  ") == normalize_name("lionel messi")


def test_empty_name():
    assert normalize_name("") == ""


def test_mismatched_vectors():
    try:
        calculate_similarity([1, 2], [1])
    except ValueError:
        return

    raise AssertionError("Expected ValueError for mismatched vectors.")


def test_identical_vectors():
    assert calculate_similarity([0.5, 0.3], [0.5, 0.3]) == 1.0

def test_sample_size_adjustment():
    player = {
        "appearances": 20,
        "goals": 20,
        "assists": 10,
    }
    baseline_rates = [0.2, 0.1]

    result = make_vector(player, baseline_rates)

    assert abs(result[0] - 0.6) < 1e-9
    assert abs(result[1] - 0.3) < 1e-9

if __name__ == "__main__":
    test_accent_insensitive_matching()
    test_uppercase_and_accents()
    test_whitespace()
    test_empty_name()
    test_mismatched_vectors()
    test_identical_vectors()
    test_sample_size_adjustment()
    print("All 7 hybrid model tests passed!")