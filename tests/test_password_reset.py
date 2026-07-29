from auth import hash_password, verify_password


def test_password_hashing():
    h = hash_password("newpass123")
    assert verify_password("newpass123", h)
    assert not verify_password("wrong", h)
