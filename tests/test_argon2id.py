import auth


def test_argon2id_hash_and_verify():
    h = auth.hash_password("securepass123", algorithm="argon2id")
    assert h.startswith("$argon2id$")
    assert auth.verify_password("securepass123", h)
    assert not auth.verify_password("wrong", h)


def test_pbkdf2_still_works():
    from werkzeug.security import generate_password_hash
    h = generate_password_hash("legacy123")
    assert auth.verify_password("legacy123", h)


def test_needs_rehash_detects_pbkdf2():
    from werkzeug.security import generate_password_hash
    h = generate_password_hash("test123")
    assert auth.needs_rehash(h) is True


def test_needs_rehash_false_for_argon2id():
    h = auth.hash_password("test123", algorithm="argon2id")
    assert auth.needs_rehash(h) is False
