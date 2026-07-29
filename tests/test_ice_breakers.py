import database


def test_random_ice_breaker(test_db):
    q = database.get_random_ice_breaker()
    assert q is not None
    assert "question" in q
