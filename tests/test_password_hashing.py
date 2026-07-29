from auth import hash_password, verify_password


def test_hash_and_verify():
    h = hash_password("test123")
    assert verify_password("test123", h) is True
    assert verify_password("wrong", h) is False


def test_different_passwords_different_hashes():
    h1 = hash_password("a")
    h2 = hash_password("a")
    # Werkzeug salts, so hashes should differ
    assert h1 != h2
    assert verify_password("a", h1)
    assert verify_password("a", h2)
