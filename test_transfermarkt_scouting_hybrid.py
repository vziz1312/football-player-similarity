from transfermarkt_scouting_hybrid import normalize_name


def test_accent_insensitive_matching():
    assert normalize_name("Kylian Mbappé") == normalize_name("kylian mbappe")


def test_uppercase_and_accents():
    assert normalize_name("BÉRGSON") == normalize_name("bergson")


def test_whitespace():
    assert normalize_name("  Lionel Messi  ") == normalize_name("lionel messi")


def test_empty_name():
    assert normalize_name("") == ""


if __name__ == "__main__":
    test_accent_insensitive_matching()
    test_uppercase_and_accents()
    test_whitespace()
    test_empty_name()
    print("All 4 name-normalization tests passed!")